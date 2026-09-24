"""Focused Windows integration tests for AIO-049 local domain ownership."""

from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
from inspect import signature
import json
import os
from pathlib import Path
import pickle
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uuid

from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainAlreadyOwnedError,
    AuthorizationDomainOwnershipIntegrityError,
    AuthorizationDomainOwnershipStateError,
    AuthorizationDomainOwnershipUnavailableError,
    OwnedAuthorizationDomainSessionClosedError,
    OwnedAuthorizationDomainSessionLostError,
)
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
)
import engineering_orchestration.windows_local_authorization_domain_owner as subject


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ID = "authorization-domain::windows-local-synthetic"
_FSCTL_SET_REPARSE_POINT = 0x000900A4
_FSCTL_DELETE_REPARSE_POINT = 0x000900AC
_IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
_UNKNOWN_REPARSE_TAG = 0x00000042
_UNKNOWN_REPARSE_GUID = uuid.UUID("f7bc6e54-2f80-4f35-b424-0f7be4f6a049")


class _FixedClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)


class _RejectingCoordinatorPorts:
    """Trusted-shape ports; lifecycle tests never admit an external action."""

    def authenticate_grant(self, presented_grant: object) -> None:
        del presented_grant
        return None

    def resolve_tool_binding(self, grant: object) -> None:
        del grant
        return None

    def collect_fresh_parent_results(
        self,
        grant: object,
        tool_binding: object,
    ) -> None:
        del grant, tool_binding
        return None

    def resolve_effective_execution_mode(
        self,
        grant: object,
        tool_binding: object,
    ) -> None:
        del grant, tool_binding
        return None

    def authenticate_original_issuer_revocation(
        self,
        presented_grant: object,
    ) -> None:
        del presented_grant
        return None


class WindowsLocalAuthorizationDomainOwnerPureTests(unittest.TestCase):
    """Platform-independent checks for the Windows adapter's pure boundaries."""

    def test_public_acquisition_has_no_registry_root_or_path_selector(self) -> None:
        self.assertEqual(
            set(subject.__all__),
            {
                "WindowsLocalAuthorizationDomainAdministration",
                "WindowsLocalAuthorizationDomainOwner",
            },
        )
        acquire_parameters = tuple(
            signature(subject.WindowsLocalAuthorizationDomainOwner.acquire).parameters
        )
        self.assertEqual(
            acquire_parameters,
            ("self", "authorization_domain_id"),
        )
        constructor_parameters = set(
            signature(subject.WindowsLocalAuthorizationDomainOwner).parameters
        )
        self.assertTrue(
            {
                "root",
                "registry_root",
                "registry_path",
                "ledger_path",
                "database_path",
            }.isdisjoint(constructor_parameters)
        )

    def test_domain_key_is_the_exact_utf8_sha256_digest(self) -> None:
        expected = hashlib.sha256(DOMAIN_ID.encode("utf-8")).hexdigest()

        self.assertEqual(subject._domain_key(DOMAIN_ID), expected)
        self.assertEqual(len(expected), 64)
        self.assertEqual(expected, expected.lower())
        self.assertNotEqual(
            subject._domain_key(DOMAIN_ID + "::other"),
            expected,
        )
        for invalid in ("", None, 1):
            with self.subTest(invalid=invalid), self.assertRaises(
                (TypeError, ValueError)
            ):
                subject._domain_key(invalid)  # type: ignore[arg-type]

    def test_records_require_exact_canonical_unique_digest_bound_json(self) -> None:
        payload = {"kind": "synthetic", "ordinal": 7}
        encoded, digest = subject._encode_record(payload)
        expected_keys = frozenset(("kind", "ordinal", "sha256"))

        self.assertEqual(
            digest,
            hashlib.sha256(subject._canonical_json_bytes(payload)).hexdigest(),
        )
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertEqual(
            subject._decode_record(encoded, expected_keys=expected_keys),
            {**payload, "sha256": digest},
        )

        duplicate = (
            '{"kind":"synthetic","kind":"synthetic","ordinal":7,'
            f'"sha256":"{digest}"}}\n'
        ).encode("utf-8")
        corrupt_document = json.loads(encoded)
        corrupt_document["sha256"] = "0" * 64
        corrupt = subject._canonical_json_bytes(corrupt_document)
        noncanonical = json.dumps(
            json.loads(encoded),
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        extra, _ = subject._encode_record({**payload, "extra": True})
        malformed_values = (
            duplicate,
            corrupt,
            noncanonical,
            extra,
            b"\xef\xbb\xbf" + encoded,
            b"\xff",
            b"",
        )
        for malformed in malformed_values:
            with self.subTest(malformed=malformed[:40]), self.assertRaises(
                AuthorizationDomainOwnershipIntegrityError
            ):
                subject._decode_record(
                    malformed,
                    expected_keys=expected_keys,
                )


@unittest.skipUnless(os.name == "nt", "Windows ownership adapter requires Windows")
class WindowsLocalAuthorizationDomainOwnerWin32Tests(unittest.TestCase):
    """Real Win32 tests confined to one disposable, explicitly secured root."""

    def setUp(self) -> None:
        workspace_root = Path(__file__).resolve().parent.parent
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="aio-049-windows-owner-",
            dir=workspace_root,
        )
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name).resolve()
        self.sid = subject._current_user_sid()
        subject._apply_security_profile(self.root, self.sid, directory=True)
        local_appdata = patch.object(
            subject,
            "_local_appdata_path",
            return_value=self.root,
        )
        local_appdata.start()
        self.addCleanup(local_appdata.stop)

    def _secure_directory(self, name: str) -> Path:
        path = self.root / name
        path.mkdir()
        subject._apply_security_profile(path, self.sid, directory=True)
        return path

    def _secure_file(
        self,
        directory: Path,
        name: str,
        data: bytes = b"synthetic-ledger",
    ) -> Path:
        path = directory / name
        path.write_bytes(data)
        subject._apply_security_profile(path, self.sid, directory=False)
        return path

    def _identity(self, path: Path):
        handle, identity = subject._open_ledger_pin(path, self.sid)
        handle.close()
        return identity

    def _binding(self, path: Path):
        identity = self._identity(path)
        return subject._LocalAuthorizationDomainBinding(
            authorization_domain_id=DOMAIN_ID,
            domain_key=subject._domain_key(DOMAIN_ID),
            current_user_sid=self.sid,
            canonical_ledger_path=identity.canonical_final_path,
            volume_serial_number=identity.volume_serial_number,
            file_id=identity.file_id,
            link_count=identity.link_count,
            ledger_instance_id="ledger-instance::windows-local-synthetic",
            domain_generation=1,
            digest="a" * 64,
        )

    def _configuration(
        self,
        suffix: str,
    ) -> SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
        ledger_directory = self._secure_directory(f"ledger-{suffix}")
        return SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
            database_path=ledger_directory / "admission.sqlite3",
            authorization_domain_id=f"{DOMAIN_ID}::{suffix}",
            ledger_instance_id=f"ledger-instance::windows-local::{suffix}",
            domain_generation=1,
            busy_timeout_ms=2_000,
        )

    def _administration(self):
        return subject.WindowsLocalAuthorizationDomainAdministration(
            clock=_FixedClock(),
            busy_timeout_ms=2_000,
        )

    def _owner(self):
        ports = _RejectingCoordinatorPorts()
        return subject.WindowsLocalAuthorizationDomainOwner(
            clock=_FixedClock(),
            grant_authentication=ports,
            tool_binding_resolver=ports,
            fresh_prerequisite_source=ports,
            execution_mode_resolver=ports,
            revocation_authentication=ports,
            busy_timeout_ms=2_000,
        )

    def _activate(
        self,
        suffix: str,
    ) -> tuple[
        subject.WindowsLocalAuthorizationDomainAdministration,
        SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        object,
    ]:
        administration = self._administration()
        configuration = self._configuration(suffix)
        provisioned = administration.provision(configuration)
        self.assertEqual(
            provisioned.outcome.value,
            "provisioned",
            provisioned.detail,
        )
        registered = administration.register(configuration)
        activated = administration.activate(
            configuration.authorization_domain_id
        )
        self.assertEqual(activated, registered)
        return administration, configuration, activated

    def _make_symlink(
        self,
        target: Path,
        link: Path,
        *,
        target_is_directory: bool,
    ) -> None:
        try:
            os.symlink(
                target,
                link,
                target_is_directory=target_is_directory,
            )
        except OSError as error:
            if error.winerror == 1314:
                self.skipTest("Windows symlink privilege is unavailable (WinError 1314)")
            raise

    def _drift_dacl(self, path: Path) -> None:
        drift = f"D:P(A;;FA;;;{self.sid})(A;;FR;;;WD)"
        with subject._SecurityDescriptor(drift) as descriptor:
            present = wintypes.BOOL()
            defaulted = wintypes.BOOL()
            dacl = wintypes.LPVOID()
            if not subject._win32()[1].GetSecurityDescriptorDacl(
                descriptor.pointer,
                ctypes.byref(present),
                ctypes.byref(dacl),
                ctypes.byref(defaulted),
            ) or not present.value:
                raise ctypes.WinError(ctypes.get_last_error())
            result = subject._win32()[1].SetNamedSecurityInfoW(
                str(path),
                subject._SE_FILE_OBJECT,
                subject._DACL_SECURITY_INFORMATION
                | subject._PROTECTED_DACL_SECURITY_INFORMATION,
                None,
                None,
                dacl,
                None,
            )
            if result != 0:
                raise ctypes.WinError(result)

    def _device_io_control(
        self,
        handle: object,
        control_code: int,
        data: bytes,
    ) -> None:
        device_io_control = subject._win32()[0].DeviceIoControl
        device_io_control.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        )
        device_io_control.restype = wintypes.BOOL
        buffer = ctypes.create_string_buffer(data, len(data))
        returned = wintypes.DWORD()
        ctypes.set_last_error(0)
        if not device_io_control(
            wintypes.HANDLE(handle.value),  # type: ignore[attr-defined]
            control_code,
            ctypes.cast(buffer, wintypes.LPVOID),
            len(data),
            None,
            0,
            ctypes.byref(returned),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def _open_reparse_carrier(self, path: Path, *, directory: bool):
        flags = subject._FILE_FLAG_OPEN_REPARSE_POINT
        if directory:
            flags |= subject._FILE_FLAG_BACKUP_SEMANTICS
        return subject._open_file(
            path,
            access=subject._GENERIC_READ | subject._GENERIC_WRITE,
            share=(
                subject._FILE_SHARE_READ
                | subject._FILE_SHARE_WRITE
                | subject._FILE_SHARE_DELETE
            ),
            creation=subject._OPEN_EXISTING,
            flags=flags,
        )

    def _set_mount_point(self, path: Path, target: Path) -> None:
        substitute = ("\\??\\" + str(target)).encode("utf-16-le")
        print_name = str(target).encode("utf-16-le")
        path_buffer = substitute + b"\x00\x00" + print_name + b"\x00\x00"
        mount_payload = struct.pack(
            "<HHHH",
            0,
            len(substitute),
            len(substitute) + 2,
            len(print_name),
        ) + path_buffer
        reparse_buffer = struct.pack(
            "<IHH",
            _IO_REPARSE_TAG_MOUNT_POINT,
            len(mount_payload),
            0,
        ) + mount_payload
        handle = self._open_reparse_carrier(path, directory=True)
        try:
            self._device_io_control(
                handle,
                _FSCTL_SET_REPARSE_POINT,
                reparse_buffer,
            )
        finally:
            handle.close()

    def _set_unknown_reparse_point(self, path: Path) -> None:
        payload = b"aio-049-unknown-reparse-data"
        reparse_buffer = (
            struct.pack(
                "<IHH",
                _UNKNOWN_REPARSE_TAG,
                len(payload),
                0,
            )
            + _UNKNOWN_REPARSE_GUID.bytes_le
            + payload
        )
        handle = self._open_reparse_carrier(path, directory=False)
        try:
            self._device_io_control(
                handle,
                _FSCTL_SET_REPARSE_POINT,
                reparse_buffer,
            )
        finally:
            handle.close()

    def _delete_reparse_point(
        self,
        path: Path,
        *,
        tag: int,
        directory: bool,
        reparse_guid: uuid.UUID | None = None,
    ) -> None:
        reparse_buffer = struct.pack("<IHH", tag, 0, 0)
        if reparse_guid is not None:
            reparse_buffer += reparse_guid.bytes_le
        handle = self._open_reparse_carrier(path, directory=directory)
        try:
            self._device_io_control(
                handle,
                _FSCTL_DELETE_REPARSE_POINT,
                reparse_buffer,
            )
        finally:
            handle.close()

    def test_share_zero_domain_lock_rejects_duplicate_and_recovers_after_close(
        self,
    ) -> None:
        lock_directory = self._secure_directory("standalone-lock")
        lock_path = lock_directory / "domain.lock"
        first = subject._open_lock(lock_path, self.sid, domain=True)
        try:
            with self.assertRaises(AuthorizationDomainAlreadyOwnedError):
                subject._open_lock(lock_path, self.sid, domain=True)
        finally:
            first.close()

        recovered = subject._open_lock(lock_path, self.sid, domain=True)
        recovered.close()

    def test_share_zero_domain_lock_recovers_after_process_hard_exit(self) -> None:
        lock_directory = self._secure_directory("hard-exit-lock")
        lock_path = lock_directory / "domain.lock"
        initialized = subject._open_lock(lock_path, self.sid, domain=True)
        initialized.close()
        child_source = "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "import sys",
                "sys.path.insert(0, sys.argv[2])",
                "import engineering_orchestration.windows_local_authorization_domain_owner as subject",
                "handle = subject._open_lock(Path(sys.argv[1]), subject._current_user_sid(), domain=True)",
                "sys.stdout.buffer.write(b'locked\\n')",
                "sys.stdout.buffer.flush()",
                "sys.stdin.buffer.read(1)",
                "os._exit(73)",
            )
        )
        process = subprocess.Popen(
            [sys.executable, "-c", child_source, str(lock_path), str(ROOT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        assert process.stdout is not None
        assert process.stdin is not None
        assert process.stderr is not None
        ready = process.stdout.readline()
        if ready != b"locked\n":
            error = process.stderr.read().decode("utf-8", errors="replace")
            self.fail(f"hard-exit lock child failed before acquisition: {error}")
        with self.assertRaises(AuthorizationDomainAlreadyOwnedError):
            subject._open_lock(lock_path, self.sid, domain=True)

        process.stdin.write(b"x")
        process.stdin.flush()
        self.assertEqual(process.wait(timeout=15), 73)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        recovered = subject._open_lock(lock_path, self.sid, domain=True)
        recovered.close()

    def test_file_identity_is_nonzero_and_hard_links_are_rejected(self) -> None:
        ledger_directory = self._secure_directory("identity-ledger")
        ledger = self._secure_file(ledger_directory, "ledger.sqlite3")
        identity = self._identity(ledger)

        self.assertGreater(identity.volume_serial_number, 0)
        self.assertEqual(len(identity.file_id), 32)
        self.assertNotEqual(identity.file_id, "0" * 32)
        self.assertEqual(identity.link_count, 1)

        alias = ledger_directory / "ledger-hard-link.sqlite3"
        os.link(ledger, alias)
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            subject._open_ledger_pin(ledger, self.sid)

    def test_held_ledger_pin_denies_rename_and_replacement(self) -> None:
        ledger_directory = self._secure_directory("pinned-ledger")
        ledger = self._secure_file(ledger_directory, "ledger.sqlite3")
        replacement = self._secure_file(
            ledger_directory,
            "replacement.sqlite3",
            b"replacement-ledger",
        )
        moved = ledger_directory / "renamed.sqlite3"
        pin, original_identity = subject._open_ledger_pin(ledger, self.sid)
        try:
            operations = (
                ("rename", lambda: ledger.replace(moved)),
                ("replacement", lambda: replacement.replace(ledger)),
            )
            for name, operation in operations:
                with self.subTest(operation=name):
                    with self.assertRaises(OSError) as raised:
                        operation()
                    self.assertIn(
                        raised.exception.winerror,
                        (
                            subject._ERROR_ACCESS_DENIED,
                            subject._ERROR_SHARING_VIOLATION,
                            subject._ERROR_LOCK_VIOLATION,
                        ),
                    )
            self.assertTrue(ledger.is_file())
            self.assertFalse(moved.exists())
            self.assertTrue(replacement.is_file())
            self.assertEqual(
                subject._identity_from_handle(pin),
                original_identity,
            )
        finally:
            pin.close()

        ledger.replace(moved)
        replacement.replace(ledger)
        self.assertTrue(moved.is_file())
        self.assertTrue(ledger.is_file())

    def test_copy_move_and_replacement_do_not_match_the_bound_identity(self) -> None:
        ledger_directory = self._secure_directory("identity-mutations")
        ledger = self._secure_file(ledger_directory, "ledger.sqlite3")
        binding = self._binding(ledger)

        copied = ledger_directory / "copied.sqlite3"
        shutil.copyfile(ledger, copied)
        subject._apply_security_profile(copied, self.sid, directory=False)
        copied_identity = self._identity(copied)
        self.assertFalse(subject._identity_matches_binding(binding, copied_identity))
        self.assertNotEqual(copied_identity.file_id, binding.file_id)

        moved = ledger_directory / "moved.sqlite3"
        ledger.replace(moved)
        moved_identity = self._identity(moved)
        self.assertFalse(subject._identity_matches_binding(binding, moved_identity))
        self.assertEqual(moved_identity.file_id, binding.file_id)

        self._secure_file(ledger_directory, "ledger.sqlite3", b"replacement")
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            subject._verify_binding_ledger(binding, self.sid)

    def test_terminal_and_ancestor_reparse_points_are_rejected(self) -> None:
        target_directory = self._secure_directory("reparse-target")
        target = self._secure_file(target_directory, "ledger.sqlite3")

        terminal = self.root / "terminal-ledger-link.sqlite3"
        self._make_symlink(target, terminal, target_is_directory=False)
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            subject._open_ledger_pin(terminal, self.sid)

        ancestor = self.root / "ancestor-ledger-link"
        self._make_symlink(
            target_directory,
            ancestor,
            target_is_directory=True,
        )
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            subject._open_ledger_pin(ancestor / target.name, self.sid)

    def test_real_junction_ancestor_is_rejected_and_removed_safely(self) -> None:
        target_directory = self._secure_directory("junction-target")
        target = self._secure_file(target_directory, "ledger.sqlite3")
        junction = self._secure_directory("junction-carrier")
        reparse_set = False
        try:
            self._set_mount_point(junction, target_directory)
            reparse_set = True
            probe = self._open_reparse_carrier(junction, directory=True)
            try:
                information = subject._file_attribute_info(probe)
                self.assertTrue(
                    information.FileAttributes
                    & subject._FILE_ATTRIBUTE_REPARSE_POINT
                )
                self.assertEqual(
                    information.ReparseTag,
                    _IO_REPARSE_TAG_MOUNT_POINT,
                )
            finally:
                probe.close()
            with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
                subject._open_ledger_pin(junction / target.name, self.sid)
        finally:
            try:
                if reparse_set:
                    self._delete_reparse_point(
                        junction,
                        tag=_IO_REPARSE_TAG_MOUNT_POINT,
                        directory=True,
                    )
            finally:
                try:
                    junction.rmdir()
                except FileNotFoundError:
                    pass

    def test_unknown_reparse_tag_is_rejected_and_removed_safely(self) -> None:
        carrier_directory = self._secure_directory("unknown-reparse")
        carrier = self._secure_file(
            carrier_directory,
            "ledger.sqlite3",
        )
        reparse_set = False
        try:
            self._set_unknown_reparse_point(carrier)
            reparse_set = True
            probe = self._open_reparse_carrier(carrier, directory=False)
            try:
                information = subject._file_attribute_info(probe)
                self.assertTrue(
                    information.FileAttributes
                    & subject._FILE_ATTRIBUTE_REPARSE_POINT
                )
                self.assertEqual(information.ReparseTag, _UNKNOWN_REPARSE_TAG)
            finally:
                probe.close()
            with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
                subject._open_ledger_pin(carrier, self.sid)
        finally:
            try:
                if reparse_set:
                    self._delete_reparse_point(
                        carrier,
                        tag=_UNKNOWN_REPARSE_TAG,
                        directory=False,
                        reparse_guid=_UNKNOWN_REPARSE_GUID,
                    )
            finally:
                carrier.unlink(missing_ok=True)

    def test_acl_drift_fails_closed_and_the_test_restores_cleanup_access(self) -> None:
        ledger_directory = self._secure_directory("acl-ledger")
        ledger = self._secure_file(ledger_directory, "ledger.sqlite3")
        subject._validate_ledger_storage_security(ledger, self.sid)

        try:
            self._drift_dacl(ledger)
            with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
                subject._open_ledger_pin(ledger, self.sid)
        finally:
            subject._apply_security_profile(ledger, self.sid, directory=False)

        try:
            self._drift_dacl(ledger_directory)
            with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
                subject._open_ledger_pin(ledger, self.sid)
        finally:
            subject._apply_security_profile(
                ledger_directory,
                self.sid,
                directory=True,
            )

    def test_activation_is_explicit_idempotent_and_digest_addressed(self) -> None:
        administration = self._administration()
        configuration = self._configuration("activation")
        provisioned = administration.provision(configuration)
        self.assertEqual(provisioned.outcome.value, "provisioned")
        identity = administration.register(configuration)

        with self.assertRaises(AuthorizationDomainOwnershipStateError):
            self._owner().acquire(configuration.authorization_domain_id)

        activated = administration.activate(
            configuration.authorization_domain_id
        )
        self.assertEqual(activated, identity)
        self.assertEqual(
            administration.activate(configuration.authorization_domain_id),
            identity,
        )
        domain_directory = (
            subject._fixed_registry_root()
            / subject._DOMAINS_DIRECTORY
            / hashlib.sha256(
                configuration.authorization_domain_id.encode("utf-8")
            ).hexdigest()
        )
        self.assertEqual(
            {item.name for item in domain_directory.iterdir()},
            {subject._BINDING_FILE, subject._ACTIVE_FILE},
        )
        self.assertNotIn(
            configuration.authorization_domain_id,
            str(domain_directory),
        )

        session = self._owner().acquire(configuration.authorization_domain_id)
        self.addCleanup(session.close)
        self.assertEqual(session.identity, identity)
        with self.assertRaises(AuthorizationDomainAlreadyOwnedError):
            self._owner().acquire(configuration.authorization_domain_id)

    def test_live_registry_reads_reject_duplicate_and_corrupt_record_bytes(
        self,
    ) -> None:
        _, configuration, _ = self._activate("record-integrity")
        domain_directory = (
            subject._fixed_registry_root()
            / subject._DOMAINS_DIRECTORY
            / subject._domain_key(configuration.authorization_domain_id)
        )
        active_path = domain_directory / subject._ACTIVE_FILE
        original = active_path.read_bytes()
        duplicate = original.replace(
            b'"state":"active"',
            b'"state":"active","state":"active"',
            1,
        )
        self.assertNotEqual(duplicate, original)
        active_path.write_bytes(duplicate)
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            self._owner().acquire(configuration.authorization_domain_id)

        active_path.write_bytes(original)
        document = json.loads(original)
        document["sha256"] = "0" * 64
        active_path.write_bytes(subject._canonical_json_bytes(document))
        with self.assertRaises(AuthorizationDomainOwnershipIntegrityError):
            self._owner().acquire(configuration.authorization_domain_id)

    def test_session_is_adapter_created_noncopyable_and_closed_fail_closed(
        self,
    ) -> None:
        _, configuration, identity = self._activate("session-shape")
        with self.assertRaises(TypeError):
            subject._WindowsOwnedAuthorizationDomainSession()

        session = self._owner().acquire(configuration.authorization_domain_id)
        self.assertEqual(session.identity, identity)
        lease = session.operation()
        for operation in (
            lambda: copy.copy(session),
            lambda: copy.deepcopy(session),
            lambda: pickle.dumps(session),
            lambda: copy.copy(lease),
            lambda: copy.deepcopy(lease),
            lambda: pickle.dumps(lease),
        ):
            with self.subTest(operation=operation), self.assertRaises(TypeError):
                operation()

        session.close()
        session.close()
        with self.assertRaises(OwnedAuthorizationDomainSessionClosedError):
            with session.operation():
                self.fail("a closed ownership session admitted an operation")
        closed_result = session.admit(object())
        self.assertEqual(closed_result.outcome.value, "storage_unavailable")

    def test_broken_live_handle_marks_session_irreversibly_lost(self) -> None:
        _, configuration, _ = self._activate("lost-session")
        session = self._owner().acquire(configuration.authorization_domain_id)
        session._pin.close()  # type: ignore[attr-defined]

        with self.assertRaises(AuthorizationDomainOwnershipUnavailableError):
            with session.operation():
                self.fail("a session with a closed ledger pin became live")
        with self.assertRaises(OwnedAuthorizationDomainSessionLostError):
            with session.operation():
                self.fail("a lost ownership session admitted a later operation")
        lost_result = session.load_authoritative_admission(object())
        self.assertEqual(lost_result.outcome.value, "storage_unavailable")
        session.close()
        replacement = self._owner().acquire(
            configuration.authorization_domain_id
        )
        replacement.close()

    def test_close_waits_for_active_operation_and_rejects_new_work(self) -> None:
        _, configuration, _ = self._activate("close-race")
        session = self._owner().acquire(configuration.authorization_domain_id)
        entered = threading.Event()
        release = threading.Event()
        worker_errors: list[BaseException] = []
        closer_errors: list[BaseException] = []

        def operate() -> None:
            try:
                with session.operation():
                    entered.set()
                    if not release.wait(10):
                        raise AssertionError("operation release timed out")
            except BaseException as error:  # pragma: no cover - assertion aid
                worker_errors.append(error)

        def close() -> None:
            try:
                session.close()
            except BaseException as error:  # pragma: no cover - assertion aid
                closer_errors.append(error)

        worker = threading.Thread(target=operate, daemon=True)
        closer = threading.Thread(target=close, daemon=True)
        worker.start()
        self.assertTrue(entered.wait(10), "operation did not acquire its lease")
        closer.start()
        deadline = time.monotonic() + 10
        while session._state == "live" and time.monotonic() < deadline:  # type: ignore[attr-defined]
            time.sleep(0.01)
        try:
            self.assertEqual(session._state, "closing")  # type: ignore[attr-defined]
            self.assertTrue(closer.is_alive(), "close did not wait for the operation")
            with self.assertRaises(OwnedAuthorizationDomainSessionClosedError):
                with session.operation():
                    self.fail("closing session admitted new work")
        finally:
            release.set()
        worker.join(10)
        closer.join(10)
        self.assertFalse(worker.is_alive(), "active operation did not quiesce")
        self.assertFalse(closer.is_alive(), "close did not complete")
        self.assertEqual(worker_errors, [])
        self.assertEqual(closer_errors, [])

    def test_session_fence_is_terminal_and_cannot_be_reactivated(self) -> None:
        administration, configuration, _ = self._activate("session-fence")
        session = self._owner().acquire(configuration.authorization_domain_id)

        session.fence()
        with self.assertRaises(OwnedAuthorizationDomainSessionClosedError):
            with session.operation():
                self.fail("a fenced session admitted a new operation")
        with self.assertRaises(AuthorizationDomainOwnershipStateError):
            self._owner().acquire(configuration.authorization_domain_id)
        with self.assertRaises(AuthorizationDomainOwnershipStateError):
            administration.activate(configuration.authorization_domain_id)
        administration.recover_fencing(configuration.authorization_domain_id)

    def test_every_durable_partial_fence_boundary_recovers_forward(self) -> None:
        fault_points = (
            "after_fencing_publish",
            "before_sqlite_fence",
            "after_sqlite_fence",
            "before_fenced_publish",
            "after_fenced_publish",
        )
        for index, fault_point in enumerate(fault_points):
            with self.subTest(fault_point=fault_point):
                administration, configuration, _ = self._activate(
                    f"fence-boundary-{index}"
                )
                observed: list[str] = []

                def fail_at_boundary(point: str) -> None:
                    observed.append(point)
                    if point == fault_point:
                        raise RuntimeError(f"synthetic fence fault: {point}")

                with patch.object(subject, "_FAULT_HOOK", fail_at_boundary):
                    with self.assertRaisesRegex(RuntimeError, fault_point):
                        administration.fence(
                            configuration.authorization_domain_id
                        )
                self.assertIn(fault_point, observed)

                expected_external = (
                    "fenced"
                    if fault_point == "after_fenced_publish"
                    else "fencing"
                )
                expected_sqlite = (
                    "active"
                    if fault_point
                    in ("after_fencing_publish", "before_sqlite_fence")
                    else "fenced"
                )
                with subject._lock_registry(
                    configuration.authorization_domain_id
                ) as registry:
                    partial = registry.load()
                    self.assertIsNotNone(partial)
                    assert partial is not None
                    self.assertEqual(partial.state, expected_external)
                    partial_store = subject._open_owned_store(
                        partial.binding,
                        clock=_FixedClock(),
                        busy_timeout_ms=2_000,
                        administrative=True,
                        allow_fenced=True,
                    )
                    self.assertEqual(
                        subject._verified_sqlite_state(partial_store),
                        expected_sqlite,
                    )

                administration.recover_fencing(
                    configuration.authorization_domain_id
                )
                administration.recover_fencing(
                    configuration.authorization_domain_id
                )
                with subject._lock_registry(
                    configuration.authorization_domain_id
                ) as registry:
                    state = registry.load()
                    self.assertIsNotNone(state)
                    assert state is not None
                    self.assertEqual(state.state, "fenced")
                    store = subject._open_owned_store(
                        state.binding,
                        clock=_FixedClock(),
                        busy_timeout_ms=2_000,
                        administrative=True,
                        allow_fenced=True,
                    )
                    self.assertEqual(subject._verified_sqlite_state(store), "fenced")
                with self.assertRaises(AuthorizationDomainOwnershipStateError):
                    self._owner().acquire(
                        configuration.authorization_domain_id
                    )


if __name__ == "__main__":
    unittest.main()
