"""Windows current-user authorization-domain ownership adapter.

This module is the sole AIO-049 v1 operational adapter.  Its supported claim
is deliberately narrow: one conforming coordinator, under one current Windows
user SID, on one local fixed NTFS host.  Live authority is the composite of a
held share-zero domain lock, a no-share-delete ledger pin, exact external
registry evidence, exact SQLite identity/state, and a live process-local
session.  Persisted bytes are never authority by themselves.

The external registry is always rooted below the OS Local AppData Known Folder.
No public API accepts a registry root.  Test code may patch the private Known
Folder resolver; that is not a supported production configuration surface.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import threading
from typing import Callable, Final
import uuid

from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentExecutionAuthorizationGrantAuthenticationPort,
    AgentExecutionDispatchAdmissionClock,
    AgentExecutionDispatchAdmissionCoordinator,
    AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    AgentExecutionDispatchAdmissionStoreAdministrationResult,
    AgentExecutionDispatchAdmissionStoreOutcome,
    EffectiveExecutionModeResolverPort,
    FreshAgentActionPrerequisiteSourcePort,
    OriginalIssuerRevocationAuthenticationPort,
    AgentOperationToolBindingResolverPort,
    _mint_owned_agent_execution_dispatch_admission_store_access,
    _mint_owned_agent_execution_dispatch_admission_store_administration_access,
    make_agent_execution_dispatch_admission_store_administration_result,
    make_agent_execution_dispatch_admission_store_result,
)
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainIdentity,
    AuthorizationDomainAlreadyOwnedError,
    AuthorizationDomainOwnershipError,
    AuthorizationDomainOwnershipIntegrityError,
    AuthorizationDomainOwnershipStateError,
    AuthorizationDomainOwnershipUnavailableError,
    AuthorizationDomainOwnershipUnsupportedError,
    OwnedAuthorizationDomainSession,
    OwnedAuthorizationDomainSessionClosedError,
    OwnedAuthorizationDomainSessionLostError,
)
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    DEFAULT_BUSY_TIMEOUT_MS,
    SqliteAgentExecutionDispatchAdmissionStore,
    SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
)


__all__ = (
    "WindowsLocalAuthorizationDomainAdministration",
    "WindowsLocalAuthorizationDomainOwner",
)


_REGISTRY_SUFFIX: Final = (
    "AI Engineering Orchestra",
    "authorization-domain-ownership",
    "v1",
)
_LOCKS_DIRECTORY: Final = "locks"
_DOMAINS_DIRECTORY: Final = "domains"
_BOOTSTRAP_LOCK: Final = "namespace-bootstrap.lock"
_BINDING_FILE: Final = "binding.v1.json"
_ACTIVE_FILE: Final = "active.v1.json"
_FENCING_FILE: Final = "fencing.v1.json"
_FENCED_FILE: Final = "fenced.v1.json"
_DOMAIN_FILES: Final = frozenset(
    (_BINDING_FILE, _ACTIVE_FILE, _FENCING_FILE, _FENCED_FILE)
)
_CANONICAL_ENCODING: Final = "utf-8-json-sort-keys-v1"
_REGISTRY_FORMAT_VERSION: Final = 1
_MAX_RECORD_BYTES: Final = 64 * 1024


# Win32 constants used by the supported adapter.
_ERROR_FILE_NOT_FOUND = 2
_ERROR_PATH_NOT_FOUND = 3
_ERROR_ACCESS_DENIED = 5
_ERROR_SHARING_VIOLATION = 32
_ERROR_LOCK_VIOLATION = 33
_ERROR_ALREADY_EXISTS = 183
_ERROR_FILE_EXISTS = 80
_ERROR_INSUFFICIENT_BUFFER = 122
_ERROR_NOT_ALL_ASSIGNED = 1300

_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_DELETE = 0x00010000
_READ_CONTROL = 0x00020000
_FILE_READ_DATA = 0x0001
_FILE_READ_ATTRIBUTES = 0x0080
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_CREATE_NEW = 1
_OPEN_EXISTING = 3
_OPEN_ALWAYS = 4
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_ATTRIBUTE_OFFLINE = 0x00001000
_FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
_DRIVE_FIXED = 3
_MOVEFILE_WRITE_THROUGH = 0x00000008
_FILE_NAME_NORMALIZED = 0
_VOLUME_NAME_DOS = 0
_FILE_STANDARD_INFO_CLASS = 1
_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
_FILE_ID_INFO_CLASS = 18

_TOKEN_QUERY = 0x0008
_TOKEN_USER_CLASS = 1
_SDDL_REVISION_1 = 1
_SE_FILE_OBJECT = 1
_OWNER_SECURITY_INFORMATION = 0x00000001
_DACL_SECURITY_INFORMATION = 0x00000004
_LABEL_SECURITY_INFORMATION = 0x00000010
_PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000

_FOLDERID_LOCAL_APP_DATA = uuid.UUID("f1b32785-6fba-4fcf-9d55-7b8e7f157091")


class _GUID(ctypes.Structure):
    _fields_ = (
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    )

    @classmethod
    def from_uuid(cls, value: uuid.UUID) -> _GUID:
        fields = value.fields
        data4 = (ctypes.c_ubyte * 8)(
            fields[3],
            fields[4],
            *fields[5].to_bytes(6, "big"),
        )
        return cls(fields[0], fields[1], fields[2], data4)


class _SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = (
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    )


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = (
        ("Sid", wintypes.LPVOID),
        ("Attributes", wintypes.DWORD),
    )


class _TOKEN_USER(ctypes.Structure):
    _fields_ = (("User", _SID_AND_ATTRIBUTES),)


class _FILE_ID_128(ctypes.Structure):
    _fields_ = (("Identifier", ctypes.c_ubyte * 16),)


class _FILE_ID_INFO(ctypes.Structure):
    _fields_ = (
        ("VolumeSerialNumber", ctypes.c_ulonglong),
        ("FileId", _FILE_ID_128),
    )


class _FILE_STANDARD_INFO(ctypes.Structure):
    _fields_ = (
        ("AllocationSize", ctypes.c_longlong),
        ("EndOfFile", ctypes.c_longlong),
        ("NumberOfLinks", wintypes.DWORD),
        ("DeletePending", ctypes.c_ubyte),
        ("Directory", ctypes.c_ubyte),
    )


class _FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
    _fields_ = (
        ("FileAttributes", wintypes.DWORD),
        ("ReparseTag", wintypes.DWORD),
    )


@dataclass(frozen=True, slots=True)
class _WindowsFileIdentity:
    canonical_final_path: str
    volume_serial_number: int
    file_id: str
    link_count: int


@dataclass(frozen=True, slots=True)
class _LocalAuthorizationDomainBinding:
    authorization_domain_id: str
    domain_key: str
    current_user_sid: str
    canonical_ledger_path: str
    volume_serial_number: int
    file_id: str
    link_count: int
    ledger_instance_id: str
    domain_generation: int
    digest: str

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return AuthorizationDomainIdentity(
            authorization_domain_id=self.authorization_domain_id,
            ledger_instance_id=self.ledger_instance_id,
            domain_generation=self.domain_generation,
        )


@dataclass(frozen=True, slots=True)
class _RegistryState:
    binding: _LocalAuthorizationDomainBinding
    state: str
    active_digest: str | None
    fencing_digest: str | None
    fenced_digest: str | None


def _require_windows() -> None:
    if os.name != "nt":
        raise AuthorizationDomainOwnershipUnsupportedError(
            "the v1 local ownership adapter supports Windows only"
        )


def _win32_error(message: str, code: int | None = None) -> OSError:
    if code is None:
        code = ctypes.get_last_error()
    return ctypes.WinError(code, message)


def _dll(name: str):
    _require_windows()
    return ctypes.WinDLL(name, use_last_error=True)


def _configure_win32():
    kernel32 = _dll("kernel32")
    advapi32 = _dll("advapi32")
    shell32 = _dll("shell32")
    ole32 = _dll("ole32")

    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetHandleInformation.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    )
    kernel32.GetHandleInformation.restype = wintypes.BOOL
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_SECURITY_ATTRIBUTES),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateDirectoryW.argtypes = (
        wintypes.LPCWSTR,
        ctypes.POINTER(_SECURITY_ATTRIBUTES),
    )
    kernel32.CreateDirectoryW.restype = wintypes.BOOL
    kernel32.GetFileAttributesW.argtypes = (wintypes.LPCWSTR,)
    kernel32.GetFileAttributesW.restype = wintypes.DWORD
    kernel32.GetFileInformationByHandleEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.GetFinalPathNameByHandleW.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.GetVolumePathNameW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
    )
    kernel32.GetVolumePathNameW.restype = wintypes.BOOL
    kernel32.GetVolumeInformationW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        wintypes.DWORD,
    )
    kernel32.GetVolumeInformationW.restype = wintypes.BOOL
    kernel32.GetDriveTypeW.argtypes = (wintypes.LPCWSTR,)
    kernel32.GetDriveTypeW.restype = wintypes.UINT
    kernel32.GetFileSizeEx.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_longlong),
    )
    kernel32.GetFileSizeEx.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = kernel32.ReadFile.argtypes
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    kernel32.MoveFileExW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    )
    kernel32.MoveFileExW.restype = wintypes.BOOL
    kernel32.DeleteFileW.argtypes = (wintypes.LPCWSTR,)
    kernel32.DeleteFileW.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (wintypes.HLOCAL,)
    kernel32.LocalFree.restype = wintypes.HLOCAL

    advapi32.OpenProcessToken.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.ConvertSidToStringSidW.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPWSTR),
    )
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.ULONG),
    )
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = (
        wintypes.BOOL
    )
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = (
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(wintypes.ULONG),
    )
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = (
        wintypes.BOOL
    )
    advapi32.GetNamedSecurityInfoW.argtypes = (
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
    )
    advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.SetNamedSecurityInfoW.argtypes = (
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.LPVOID,
    )
    advapi32.SetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.GetSecurityDescriptorOwner.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi32.GetSecurityDescriptorOwner.restype = wintypes.BOOL
    advapi32.GetSecurityDescriptorDacl.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL
    advapi32.GetSecurityDescriptorSacl.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi32.GetSecurityDescriptorSacl.restype = wintypes.BOOL

    shell32.SHGetKnownFolderPath.argtypes = (
        ctypes.POINTER(_GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.LPWSTR),
    )
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = (wintypes.LPVOID,)
    ole32.CoTaskMemFree.restype = None
    return kernel32, advapi32, shell32, ole32


_WIN32 = None


def _win32():
    global _WIN32
    if _WIN32 is None:
        _WIN32 = _configure_win32()
    return _WIN32


class _Handle:
    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        if not value or value == ctypes.c_void_p(-1).value:
            raise ValueError("a live Win32 handle is required")
        self._value = value

    @property
    def value(self) -> int:
        if self._value is None:
            raise AuthorizationDomainOwnershipUnavailableError(
                "the required Win32 handle is closed"
            )
        return self._value

    @property
    def closed(self) -> bool:
        return self._value is None

    def check_live(self) -> None:
        flags = wintypes.DWORD()
        if not _win32()[0].GetHandleInformation(
            wintypes.HANDLE(self.value), ctypes.byref(flags)
        ):
            raise AuthorizationDomainOwnershipUnavailableError(
                "a required ownership handle is no longer live"
            )

    def close(self) -> None:
        value = self._value
        if value is None:
            return
        self._value = None
        if not _win32()[0].CloseHandle(wintypes.HANDLE(value)):
            raise _win32_error("CloseHandle failed")

    def __enter__(self) -> _Handle:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


def _current_user_sid() -> str:
    kernel32, advapi32, _, _ = _win32()
    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)
    ):
        raise AuthorizationDomainOwnershipUnavailableError(
            "the current process token could not be opened"
        ) from _win32_error("OpenProcessToken failed")
    try:
        needed = wintypes.DWORD()
        ctypes.set_last_error(0)
        advapi32.GetTokenInformation(
            token,
            _TOKEN_USER_CLASS,
            None,
            0,
            ctypes.byref(needed),
        )
        if ctypes.get_last_error() != _ERROR_INSUFFICIENT_BUFFER or needed.value == 0:
            raise _win32_error("GetTokenInformation sizing failed")
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(
            token,
            _TOKEN_USER_CLASS,
            buffer,
            needed,
            ctypes.byref(needed),
        ):
            raise _win32_error("GetTokenInformation failed")
        token_user = ctypes.cast(buffer, ctypes.POINTER(_TOKEN_USER)).contents
        rendered = wintypes.LPWSTR()
        if not advapi32.ConvertSidToStringSidW(
            token_user.User.Sid,
            ctypes.byref(rendered),
        ):
            raise _win32_error("ConvertSidToStringSidW failed")
        try:
            sid = rendered.value
            if not sid:
                raise AuthorizationDomainOwnershipIntegrityError(
                    "the current user SID is empty"
                )
            return sid
        finally:
            kernel32.LocalFree(ctypes.cast(rendered, wintypes.HLOCAL))
    finally:
        kernel32.CloseHandle(token)


def _local_appdata_path() -> Path:
    _, _, shell32, ole32 = _win32()
    folder_id = _GUID.from_uuid(_FOLDERID_LOCAL_APP_DATA)
    rendered = wintypes.LPWSTR()
    result = shell32.SHGetKnownFolderPath(
        ctypes.byref(folder_id),
        0,
        None,
        ctypes.byref(rendered),
    )
    if result < 0:
        raise AuthorizationDomainOwnershipUnavailableError(
            "Local AppData Known Folder resolution failed"
        )
    try:
        value = rendered.value
        if not value:
            raise AuthorizationDomainOwnershipUnavailableError(
                "Local AppData Known Folder is empty"
            )
        return Path(value)
    finally:
        ole32.CoTaskMemFree(ctypes.cast(rendered, wintypes.LPVOID))


def _fixed_registry_root() -> Path:
    root = _local_appdata_path()
    for component in _REGISTRY_SUFFIX:
        root = root / component
    return root


def _domain_key(authorization_domain_id: str) -> str:
    if type(authorization_domain_id) is not str or not authorization_domain_id:
        raise ValueError("authorization_domain_id must be an exact nonempty string")
    return hashlib.sha256(authorization_domain_id.encode("utf-8")).hexdigest()


def _security_sddl(sid: str, *, directory: bool) -> str:
    ace_flags = "OICI" if directory else ""
    label_flags = "OICI" if directory else ""
    return (
        f"O:{sid}"
        "D:P"
        f"(A;{ace_flags};FA;;;{sid})"
        f"(A;{ace_flags};FA;;;SY)"
        f"(A;{ace_flags};FA;;;BA)"
        f"S:(ML;{label_flags};NW;;;ME)"
    )


class _SecurityDescriptor(AbstractContextManager["_SecurityDescriptor"]):
    __slots__ = ("pointer", "attributes")

    def __init__(self, sddl: str) -> None:
        pointer = wintypes.LPVOID()
        size = wintypes.ULONG()
        if not _win32()[1].ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl,
            _SDDL_REVISION_1,
            ctypes.byref(pointer),
            ctypes.byref(size),
        ):
            raise _win32_error(
                "ConvertStringSecurityDescriptorToSecurityDescriptorW failed"
            )
        self.pointer = pointer
        self.attributes = _SECURITY_ATTRIBUTES(
            ctypes.sizeof(_SECURITY_ATTRIBUTES),
            pointer,
            False,
        )

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.pointer:
            _win32()[0].LocalFree(ctypes.cast(self.pointer, wintypes.HLOCAL))
            self.pointer = wintypes.LPVOID()


def _canonicalize_security_descriptor(pointer: wintypes.LPVOID) -> str:
    rendered = wintypes.LPWSTR()
    length = wintypes.ULONG()
    information = (
        _OWNER_SECURITY_INFORMATION
        | _DACL_SECURITY_INFORMATION
        | _LABEL_SECURITY_INFORMATION
    )
    if not _win32()[1].ConvertSecurityDescriptorToStringSecurityDescriptorW(
        pointer,
        _SDDL_REVISION_1,
        information,
        ctypes.byref(rendered),
        ctypes.byref(length),
    ):
        raise _win32_error(
            "ConvertSecurityDescriptorToStringSecurityDescriptorW failed"
        )
    try:
        value = rendered.value
        if not value:
            raise AuthorizationDomainOwnershipIntegrityError(
                "security descriptor canonicalization returned no value"
            )
        return value
    finally:
        _win32()[0].LocalFree(ctypes.cast(rendered, wintypes.HLOCAL))


def _canonical_security_sddl(sddl: str) -> str:
    with _SecurityDescriptor(sddl) as descriptor:
        return _canonicalize_security_descriptor(descriptor.pointer)


def _path_security_sddl(path: Path) -> str:
    owner = wintypes.LPVOID()
    dacl = wintypes.LPVOID()
    sacl = wintypes.LPVOID()
    descriptor = wintypes.LPVOID()
    information = (
        _OWNER_SECURITY_INFORMATION
        | _DACL_SECURITY_INFORMATION
        | _LABEL_SECURITY_INFORMATION
    )
    result = _win32()[1].GetNamedSecurityInfoW(
        str(path),
        _SE_FILE_OBJECT,
        information,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        ctypes.byref(sacl),
        ctypes.byref(descriptor),
    )
    if result != 0:
        raise AuthorizationDomainOwnershipIntegrityError(
            f"security descriptor query failed for {path.name!r}: WinError {result}"
        )
    try:
        return _canonicalize_security_descriptor(descriptor)
    finally:
        _win32()[0].LocalFree(ctypes.cast(descriptor, wintypes.HLOCAL))


def _validate_security_profile(
    path: Path,
    sid: str,
    *,
    directory: bool,
    allow_safe_inheritance: bool = False,
) -> None:
    actual = _path_security_sddl(path)
    intended = _canonical_security_sddl(
        _security_sddl(sid, directory=directory)
    )
    dacl_auto_inherited = intended.replace("D:P", "D:PAI", 1)
    sacl_auto_inherited = intended.replace("S:", "S:AI", 1)
    candidates = {
        intended,
        dacl_auto_inherited,
        sacl_auto_inherited,
        dacl_auto_inherited.replace("S:", "S:AI", 1),
    }
    if allow_safe_inheritance and not directory:
        candidates.add(
            _canonical_security_sddl(
                f"O:{sid}"
                "D:AI"
                f"(A;ID;FA;;;{sid})(A;ID;FA;;;SY)(A;ID;FA;;;BA)"
                "S:AI(ML;ID;NW;;;ME)"
            )
        )
    if actual not in candidates:
        raise AuthorizationDomainOwnershipIntegrityError(
            f"security descriptor drift detected for {path.name!r}"
        )


def _apply_security_profile(path: Path, sid: str, *, directory: bool) -> None:
    with _SecurityDescriptor(_security_sddl(sid, directory=directory)) as expected:
        owner = wintypes.LPVOID()
        dacl = wintypes.LPVOID()
        sacl = wintypes.LPVOID()
        defaulted = wintypes.BOOL()
        present = wintypes.BOOL()
        if not _win32()[1].GetSecurityDescriptorOwner(
            expected.pointer, ctypes.byref(owner), ctypes.byref(defaulted)
        ):
            raise _win32_error("GetSecurityDescriptorOwner failed")
        if not _win32()[1].GetSecurityDescriptorDacl(
            expected.pointer,
            ctypes.byref(present),
            ctypes.byref(dacl),
            ctypes.byref(defaulted),
        ) or not present.value:
            raise _win32_error("GetSecurityDescriptorDacl failed")
        if not _win32()[1].GetSecurityDescriptorSacl(
            expected.pointer,
            ctypes.byref(present),
            ctypes.byref(sacl),
            ctypes.byref(defaulted),
        ) or not present.value:
            raise _win32_error("GetSecurityDescriptorSacl failed")
        result = _win32()[1].SetNamedSecurityInfoW(
            str(path),
            _SE_FILE_OBJECT,
            _OWNER_SECURITY_INFORMATION
            | _DACL_SECURITY_INFORMATION
            | _PROTECTED_DACL_SECURITY_INFORMATION
            | _LABEL_SECURITY_INFORMATION,
            owner,
            None,
            dacl,
            sacl,
        )
        if result != 0:
            raise AuthorizationDomainOwnershipUnavailableError(
                f"security profile publication failed: WinError {result}"
            )
    _validate_security_profile(path, sid, directory=directory)


def _create_secure_directory(path: Path, sid: str) -> None:
    attributes = _win32()[0].GetFileAttributesW(str(path))
    if attributes != _INVALID_FILE_ATTRIBUTES:
        if not attributes & _FILE_ATTRIBUTE_DIRECTORY:
            raise AuthorizationDomainOwnershipIntegrityError(
                f"registry component {path.name!r} is not a directory"
            )
        if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise AuthorizationDomainOwnershipIntegrityError(
                f"registry component {path.name!r} is a reparse point"
            )
        _validate_security_profile(path, sid, directory=True)
        return
    with _SecurityDescriptor(_security_sddl(sid, directory=True)) as descriptor:
        if not _win32()[0].CreateDirectoryW(
            str(path), ctypes.byref(descriptor.attributes)
        ):
            code = ctypes.get_last_error()
            if code != _ERROR_ALREADY_EXISTS:
                raise AuthorizationDomainOwnershipUnavailableError(
                    f"registry directory creation failed: WinError {code}"
                )
    attributes = _win32()[0].GetFileAttributesW(str(path))
    if (
        attributes == _INVALID_FILE_ATTRIBUTES
        or not attributes & _FILE_ATTRIBUTE_DIRECTORY
        or attributes & _FILE_ATTRIBUTE_REPARSE_POINT
    ):
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry directory publication was replaced or aliased"
        )
    _validate_security_profile(path, sid, directory=True)


def _create_registry_namespace(sid: str) -> Path:
    local_appdata = _local_appdata_path()
    root = local_appdata
    for component in _REGISTRY_SUFFIX:
        root = root / component
        _create_secure_directory(root, sid)
    _create_secure_directory(root / _LOCKS_DIRECTORY, sid)
    _create_secure_directory(root / _DOMAINS_DIRECTORY, sid)
    _validate_local_ntfs_path(root)
    _reject_reparse_components(root, terminal_directory=True)
    return root


def _open_file(
    path: Path,
    *,
    access: int,
    share: int,
    creation: int,
    flags: int,
    security: _SECURITY_ATTRIBUTES | None = None,
) -> _Handle:
    security_pointer = ctypes.byref(security) if security is not None else None
    value = _win32()[0].CreateFileW(
        str(path),
        access,
        share,
        security_pointer,
        creation,
        flags,
        None,
    )
    numeric = value if isinstance(value, int) else value.value
    if numeric == ctypes.c_void_p(-1).value:
        raise _win32_error(f"CreateFileW failed for {path.name!r}")
    assert numeric is not None
    return _Handle(numeric)


def _file_attribute_info(handle: _Handle) -> _FILE_ATTRIBUTE_TAG_INFO:
    result = _FILE_ATTRIBUTE_TAG_INFO()
    if not _win32()[0].GetFileInformationByHandleEx(
        wintypes.HANDLE(handle.value),
        _FILE_ATTRIBUTE_TAG_INFO_CLASS,
        ctypes.byref(result),
        ctypes.sizeof(result),
    ):
        raise _win32_error("FileAttributeTagInfo query failed")
    return result


def _file_standard_info(handle: _Handle) -> _FILE_STANDARD_INFO:
    result = _FILE_STANDARD_INFO()
    if not _win32()[0].GetFileInformationByHandleEx(
        wintypes.HANDLE(handle.value),
        _FILE_STANDARD_INFO_CLASS,
        ctypes.byref(result),
        ctypes.sizeof(result),
    ):
        raise _win32_error("FileStandardInfo query failed")
    return result


def _file_id_info(handle: _Handle) -> _FILE_ID_INFO:
    result = _FILE_ID_INFO()
    if not _win32()[0].GetFileInformationByHandleEx(
        wintypes.HANDLE(handle.value),
        _FILE_ID_INFO_CLASS,
        ctypes.byref(result),
        ctypes.sizeof(result),
    ):
        raise _win32_error("FileIdInfo query failed")
    return result


def _final_path(handle: _Handle) -> str:
    flags = _FILE_NAME_NORMALIZED | _VOLUME_NAME_DOS
    needed = _win32()[0].GetFinalPathNameByHandleW(
        wintypes.HANDLE(handle.value), None, 0, flags
    )
    if needed == 0:
        raise _win32_error("GetFinalPathNameByHandleW sizing failed")
    buffer = ctypes.create_unicode_buffer(needed + 1)
    written = _win32()[0].GetFinalPathNameByHandleW(
        wintypes.HANDLE(handle.value), buffer, len(buffer), flags
    )
    if written == 0 or written >= len(buffer):
        raise _win32_error("GetFinalPathNameByHandleW failed")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\") or not value.startswith("\\\\?\\"):
        raise AuthorizationDomainOwnershipUnsupportedError(
            "only final DOS paths on local volumes are supported"
        )
    return value


def _normal_path_from_final(path: str) -> Path:
    if not path.startswith("\\\\?\\") or path.startswith("\\\\?\\UNC\\"):
        raise AuthorizationDomainOwnershipIntegrityError(
            "stored canonical ledger path is not an extended local DOS path"
        )
    normal = path[4:]
    parsed = PureWindowsPath(normal)
    if not parsed.is_absolute() or not parsed.drive or parsed.root != "\\":
        raise AuthorizationDomainOwnershipIntegrityError(
            "stored canonical ledger path is not drive-absolute"
        )
    return Path(normal)


def _validate_local_ntfs_path(path: Path) -> None:
    raw = str(path)
    parsed = PureWindowsPath(raw)
    if (
        raw.startswith("\\\\")
        or raw.startswith("//")
        or not parsed.is_absolute()
        or not parsed.drive
        or parsed.root != "\\"
        or any(":" in component for component in parsed.parts[1:])
    ):
        raise AuthorizationDomainOwnershipUnsupportedError(
            "UNC, network, relative, and alternate-stream paths are unsupported"
        )
    volume = ctypes.create_unicode_buffer(32768)
    if not _win32()[0].GetVolumePathNameW(raw, volume, len(volume)):
        raise AuthorizationDomainOwnershipUnsupportedError(
            "the path volume could not be established"
        )
    if _win32()[0].GetDriveTypeW(volume.value) != _DRIVE_FIXED:
        raise AuthorizationDomainOwnershipUnsupportedError(
            "the supported profile requires a local fixed volume"
        )
    filesystem = ctypes.create_unicode_buffer(256)
    serial = wintypes.DWORD()
    maximum_component = wintypes.DWORD()
    flags = wintypes.DWORD()
    if not _win32()[0].GetVolumeInformationW(
        volume.value,
        None,
        0,
        ctypes.byref(serial),
        ctypes.byref(maximum_component),
        ctypes.byref(flags),
        filesystem,
        len(filesystem),
    ):
        raise AuthorizationDomainOwnershipUnsupportedError(
            "the path filesystem could not be established"
        )
    if filesystem.value.upper() != "NTFS":
        raise AuthorizationDomainOwnershipUnsupportedError(
            "the supported profile requires NTFS"
        )


def _windows_components(path: Path) -> tuple[Path, ...]:
    parsed = PureWindowsPath(str(path))
    if not parsed.is_absolute() or not parsed.drive or parsed.root != "\\":
        raise AuthorizationDomainOwnershipUnsupportedError(
            "a drive-absolute Windows path is required"
        )
    current = Path(parsed.anchor)
    values = [current]
    for component in parsed.parts[1:]:
        current = current / component
        values.append(current)
    return tuple(values)


def _reject_reparse_components(path: Path, *, terminal_directory: bool) -> None:
    components = _windows_components(path)
    for index, component in enumerate(components):
        terminal = index == len(components) - 1
        handle = _open_file(
            component,
            # Query-only handles avoid requiring ACL grants on accessible
            # ancestors while OPEN_REPARSE_POINT preserves named-object checks.
            access=0,
            share=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
            creation=_OPEN_EXISTING,
            flags=_FILE_FLAG_OPEN_REPARSE_POINT | _FILE_FLAG_BACKUP_SEMANTICS,
        )
        try:
            attributes = _file_attribute_info(handle)
            if attributes.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise AuthorizationDomainOwnershipIntegrityError(
                    f"reparse-point path component rejected: {component.name!r}"
                )
            cloud_flags = (
                _FILE_ATTRIBUTE_OFFLINE
                | _FILE_ATTRIBUTE_RECALL_ON_OPEN
                | _FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
            )
            if attributes.FileAttributes & cloud_flags:
                raise AuthorizationDomainOwnershipUnsupportedError(
                    f"offline or recall-on-access path rejected: {component.name!r}"
                )
            standard = _file_standard_info(handle)
            should_be_directory = not terminal or terminal_directory
            if bool(standard.Directory) is not should_be_directory:
                kind = "directory" if should_be_directory else "regular file"
                raise AuthorizationDomainOwnershipIntegrityError(
                    f"path component {component.name!r} is not a {kind}"
                )
        finally:
            handle.close()


def _identity_from_handle(handle: _Handle) -> _WindowsFileIdentity:
    attributes = _file_attribute_info(handle)
    if attributes.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise AuthorizationDomainOwnershipIntegrityError(
            "the ledger terminal is a reparse point"
        )
    cloud_flags = (
        _FILE_ATTRIBUTE_OFFLINE
        | _FILE_ATTRIBUTE_RECALL_ON_OPEN
        | _FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
    )
    if attributes.FileAttributes & cloud_flags:
        raise AuthorizationDomainOwnershipUnsupportedError(
            "offline or recall-on-access ledgers are unsupported"
        )
    standard = _file_standard_info(handle)
    if standard.Directory or standard.DeletePending:
        raise AuthorizationDomainOwnershipIntegrityError(
            "the ledger is not a stable regular file"
        )
    if standard.NumberOfLinks != 1:
        raise AuthorizationDomainOwnershipIntegrityError(
            "the ledger must have exactly one hard link"
        )
    file_id = _file_id_info(handle)
    identifier = bytes(file_id.FileId.Identifier)
    if file_id.VolumeSerialNumber == 0 or not any(identifier):
        raise AuthorizationDomainOwnershipIntegrityError(
            "the ledger FILE_ID_INFO identity must be nonzero"
        )
    return _WindowsFileIdentity(
        canonical_final_path=_final_path(handle),
        volume_serial_number=int(file_id.VolumeSerialNumber),
        file_id=identifier.hex(),
        link_count=int(standard.NumberOfLinks),
    )


def _validate_ledger_storage_security(path: Path, sid: str) -> None:
    _validate_security_profile(path.parent, sid, directory=True)
    _validate_security_profile(
        path,
        sid,
        directory=False,
        allow_safe_inheritance=True,
    )
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(path) + suffix)
        attributes = _win32()[0].GetFileAttributesW(str(sidecar))
        if attributes == _INVALID_FILE_ATTRIBUTES:
            code = ctypes.get_last_error()
            if code in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
                continue
            raise AuthorizationDomainOwnershipUnavailableError(
                f"ledger sidecar state is unavailable: WinError {code}"
            )
        if attributes & (_FILE_ATTRIBUTE_DIRECTORY | _FILE_ATTRIBUTE_REPARSE_POINT):
            raise AuthorizationDomainOwnershipIntegrityError(
                f"ledger sidecar {sidecar.name!r} is aliased or not regular"
            )
        _validate_security_profile(
            sidecar,
            sid,
            directory=False,
            allow_safe_inheritance=True,
        )


def _open_ledger_pin(path: Path, sid: str) -> tuple[_Handle, _WindowsFileIdentity]:
    _validate_local_ntfs_path(path)
    _reject_reparse_components(path, terminal_directory=False)
    _validate_ledger_storage_security(path, sid)
    handle = _open_file(
        path,
        access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _READ_CONTROL,
        share=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
        creation=_OPEN_EXISTING,
        flags=_FILE_FLAG_OPEN_REPARSE_POINT,
    )
    try:
        identity = _identity_from_handle(handle)
        if _normal_path_from_final(identity.canonical_final_path) != path:
            # Compare the handle-derived final path again below; lexical aliases
            # are never promoted to authority.
            requested = str(path)
            final_normal = str(_normal_path_from_final(identity.canonical_final_path))
            if requested.casefold() != final_normal.casefold():
                raise AuthorizationDomainOwnershipIntegrityError(
                    "the requested ledger path is not its canonical final path"
                )
        return handle, identity
    except BaseException:
        handle.close()
        raise


def _reject_nonfinite(value: str) -> None:
    raise AuthorizationDomainOwnershipIntegrityError(
        f"non-finite JSON value is forbidden: {value}"
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AuthorizationDomainOwnershipIntegrityError(
                f"duplicate JSON member rejected: {key!r}"
            )
        result[key] = value
    return result


def _canonical_json_bytes(document: object) -> bytes:
    try:
        text = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record cannot be canonically encoded"
        ) from error
    return text.encode("utf-8") + b"\n"


def _encode_record(payload: dict[str, object]) -> tuple[bytes, str]:
    if "sha256" in payload:
        raise ValueError("record payload must not predefine sha256")
    payload_bytes = _canonical_json_bytes(payload)
    digest = hashlib.sha256(payload_bytes).hexdigest()
    complete = dict(payload)
    complete["sha256"] = digest
    return _canonical_json_bytes(complete), digest


def _decode_record(data: bytes, *, expected_keys: frozenset[str]) -> dict[str, object]:
    if not data or len(data) > _MAX_RECORD_BYTES or data.startswith(b"\xef\xbb\xbf"):
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record size or UTF-8 framing is invalid"
        )
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record is not canonical UTF-8 JSON"
        ) from error
    if type(value) is not dict or frozenset(value) != expected_keys:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record fields are missing or unknown"
        )
    if _canonical_json_bytes(value) != data:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record is not in the required canonical encoding"
        )
    digest = value.get("sha256")
    if type(digest) is not str or len(digest) != 64:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record digest is malformed"
        )
    payload = dict(value)
    del payload["sha256"]
    if hashlib.sha256(_canonical_json_bytes(payload)).hexdigest() != digest:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record digest mismatch"
        )
    return value


_BINDING_KEYS = frozenset(
    (
        "authorization_domain_id",
        "canonical_encoding",
        "canonical_ledger_path",
        "current_user_sid",
        "domain_generation",
        "domain_key",
        "file_id",
        "format_version",
        "initial_state",
        "ledger_instance_id",
        "link_count",
        "record_kind",
        "record_version",
        "sha256",
        "volume_serial_number",
    )
)
_MARKER_KEYS = frozenset(
    (
        "authorization_domain_id",
        "binding_sha256",
        "canonical_encoding",
        "current_user_sid",
        "domain_key",
        "format_version",
        "predecessor_kind",
        "predecessor_sha256",
        "record_kind",
        "record_version",
        "sha256",
        "state",
    )
)


def _binding_payload(
    configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    sid: str,
    file_identity: _WindowsFileIdentity,
) -> dict[str, object]:
    return {
        "authorization_domain_id": configuration.authorization_domain_id,
        "canonical_encoding": _CANONICAL_ENCODING,
        "canonical_ledger_path": file_identity.canonical_final_path,
        "current_user_sid": sid,
        "domain_generation": configuration.domain_generation,
        "domain_key": _domain_key(configuration.authorization_domain_id),
        "file_id": file_identity.file_id,
        "format_version": _REGISTRY_FORMAT_VERSION,
        "initial_state": "inactive",
        "ledger_instance_id": configuration.ledger_instance_id,
        "link_count": file_identity.link_count,
        "record_kind": "local_authorization_domain_binding",
        "record_version": 1,
        "volume_serial_number": file_identity.volume_serial_number,
    }


def _parse_binding(
    document: dict[str, object],
    *,
    authorization_domain_id: str,
    sid: str,
) -> _LocalAuthorizationDomainBinding:
    domain_key = _domain_key(authorization_domain_id)
    if (
        document["format_version"] != _REGISTRY_FORMAT_VERSION
        or document["record_version"] != 1
        or document["record_kind"] != "local_authorization_domain_binding"
        or document["canonical_encoding"] != _CANONICAL_ENCODING
        or document["authorization_domain_id"] != authorization_domain_id
        or document["domain_key"] != domain_key
        or document["current_user_sid"] != sid
        or document["initial_state"] != "inactive"
        or type(document["canonical_ledger_path"]) is not str
        or type(document["volume_serial_number"]) is not int
        or document["volume_serial_number"] <= 0
        or type(document["file_id"]) is not str
        or len(document["file_id"]) != 32
        or document["file_id"] == "0" * 32
        or type(document["link_count"]) is not int
        or document["link_count"] != 1
        or type(document["ledger_instance_id"]) is not str
        or not document["ledger_instance_id"]
        or type(document["domain_generation"]) is not int
        or document["domain_generation"] <= 0
        or type(document["sha256"]) is not str
    ):
        raise AuthorizationDomainOwnershipIntegrityError(
            "the immutable domain binding is malformed or misplaced"
        )
    try:
        bytes.fromhex(document["file_id"])
        _normal_path_from_final(document["canonical_ledger_path"])
    except (TypeError, ValueError) as error:
        raise AuthorizationDomainOwnershipIntegrityError(
            "the immutable domain binding file identity is malformed"
        ) from error
    return _LocalAuthorizationDomainBinding(
        authorization_domain_id=authorization_domain_id,
        domain_key=domain_key,
        current_user_sid=sid,
        canonical_ledger_path=document["canonical_ledger_path"],
        volume_serial_number=document["volume_serial_number"],
        file_id=document["file_id"],
        link_count=document["link_count"],
        ledger_instance_id=document["ledger_instance_id"],
        domain_generation=document["domain_generation"],
        digest=document["sha256"],
    )


def _marker_payload(
    binding: _LocalAuthorizationDomainBinding,
    *,
    state: str,
    predecessor_kind: str,
    predecessor_sha256: str,
) -> dict[str, object]:
    return {
        "authorization_domain_id": binding.authorization_domain_id,
        "binding_sha256": binding.digest,
        "canonical_encoding": _CANONICAL_ENCODING,
        "current_user_sid": binding.current_user_sid,
        "domain_key": binding.domain_key,
        "format_version": _REGISTRY_FORMAT_VERSION,
        "predecessor_kind": predecessor_kind,
        "predecessor_sha256": predecessor_sha256,
        "record_kind": f"local_authorization_domain_{state}",
        "record_version": 1,
        "state": state,
    }


def _parse_marker(
    document: dict[str, object],
    binding: _LocalAuthorizationDomainBinding,
    *,
    state: str,
    predecessor_kind: str,
    predecessor_sha256: str,
) -> str:
    if (
        document["format_version"] != _REGISTRY_FORMAT_VERSION
        or document["record_version"] != 1
        or document["record_kind"] != f"local_authorization_domain_{state}"
        or document["canonical_encoding"] != _CANONICAL_ENCODING
        or document["authorization_domain_id"] != binding.authorization_domain_id
        or document["domain_key"] != binding.domain_key
        or document["current_user_sid"] != binding.current_user_sid
        or document["binding_sha256"] != binding.digest
        or document["predecessor_kind"] != predecessor_kind
        or document["predecessor_sha256"] != predecessor_sha256
        or document["state"] != state
        or type(document["sha256"]) is not str
    ):
        raise AuthorizationDomainOwnershipIntegrityError(
            f"the {state!r} state marker is malformed or contradictory"
        )
    return document["sha256"]


def _read_handle_bytes(handle: _Handle) -> bytes:
    size = ctypes.c_longlong()
    if not _win32()[0].GetFileSizeEx(
        wintypes.HANDLE(handle.value), ctypes.byref(size)
    ):
        raise _win32_error("GetFileSizeEx failed")
    if size.value <= 0 or size.value > _MAX_RECORD_BYTES:
        raise AuthorizationDomainOwnershipIntegrityError(
            "registry record length is invalid"
        )
    buffer = ctypes.create_string_buffer(size.value)
    read = wintypes.DWORD()
    if not _win32()[0].ReadFile(
        wintypes.HANDLE(handle.value),
        buffer,
        size.value,
        ctypes.byref(read),
        None,
    ) or read.value != size.value:
        raise _win32_error("registry record read failed")
    return buffer.raw[: read.value]


def _read_registry_record(path: Path, sid: str) -> bytes:
    handle = _open_file(
        path,
        access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _READ_CONTROL,
        share=_FILE_SHARE_READ,
        creation=_OPEN_EXISTING,
        flags=_FILE_FLAG_OPEN_REPARSE_POINT,
    )
    try:
        attributes = _file_attribute_info(handle)
        standard = _file_standard_info(handle)
        if (
            attributes.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT
            or standard.Directory
            or standard.NumberOfLinks != 1
        ):
            raise AuthorizationDomainOwnershipIntegrityError(
                f"registry record {path.name!r} is aliased or not regular"
            )
        _validate_security_profile(path, sid, directory=False)
        return _read_handle_bytes(handle)
    finally:
        handle.close()


def _record_exists(path: Path) -> bool:
    attributes = _win32()[0].GetFileAttributesW(str(path))
    if attributes != _INVALID_FILE_ATTRIBUTES:
        return True
    code = ctypes.get_last_error()
    if code in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
        return False
    raise AuthorizationDomainOwnershipUnavailableError(
        f"registry record state is unavailable: WinError {code}"
    )


def _write_handle_bytes(handle: _Handle, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        chunk = data[offset : offset + (1024 * 1024)]
        buffer = ctypes.create_string_buffer(chunk)
        written = wintypes.DWORD()
        if not _win32()[0].WriteFile(
            wintypes.HANDLE(handle.value),
            buffer,
            len(chunk),
            ctypes.byref(written),
            None,
        ) or written.value != len(chunk):
            raise _win32_error("registry record write failed")
        offset += written.value
    if not _win32()[0].FlushFileBuffers(wintypes.HANDLE(handle.value)):
        raise _win32_error("registry record flush failed")


def _delete_file_if_present(path: Path) -> None:
    if _win32()[0].DeleteFileW(str(path)):
        return
    code = ctypes.get_last_error()
    if code not in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
        raise _win32_error("temporary registry cleanup failed", code)


def _publish_record(path: Path, data: bytes, sid: str) -> None:
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    created = False
    try:
        with _SecurityDescriptor(_security_sddl(sid, directory=False)) as descriptor:
            handle = _open_file(
                temporary,
                access=_GENERIC_READ | _GENERIC_WRITE | _DELETE,
                share=0,
                creation=_CREATE_NEW,
                flags=_FILE_ATTRIBUTE_NORMAL | _FILE_FLAG_OPEN_REPARSE_POINT,
                security=descriptor.attributes,
            )
        created = True
        try:
            _write_handle_bytes(handle, data)
        finally:
            handle.close()
        _validate_security_profile(temporary, sid, directory=False)
        if not _win32()[0].MoveFileExW(
            str(temporary), str(path), _MOVEFILE_WRITE_THROUGH
        ):
            code = ctypes.get_last_error()
            if code not in (_ERROR_ALREADY_EXISTS, _ERROR_FILE_EXISTS):
                raise AuthorizationDomainOwnershipUnavailableError(
                    f"atomic no-replace publication failed: WinError {code}"
                )
            if _read_registry_record(path, sid) != data:
                raise AuthorizationDomainOwnershipIntegrityError(
                    "an existing registry record differs from the exact target"
                )
            _delete_file_if_present(temporary)
        created = False
        if _read_registry_record(path, sid) != data:
            raise AuthorizationDomainOwnershipIntegrityError(
                "post-publication registry byte verification failed"
            )
    finally:
        if created:
            try:
                _delete_file_if_present(temporary)
            except OSError:
                pass


def _open_lock(path: Path, sid: str, *, domain: bool) -> _Handle:
    try:
        with _SecurityDescriptor(_security_sddl(sid, directory=False)) as descriptor:
            handle = _open_file(
                path,
                access=_GENERIC_READ | _GENERIC_WRITE | _DELETE,
                share=0,
                creation=_OPEN_ALWAYS,
                flags=_FILE_ATTRIBUTE_NORMAL | _FILE_FLAG_OPEN_REPARSE_POINT,
                security=descriptor.attributes,
            )
    except OSError as error:
        if error.winerror in (_ERROR_SHARING_VIOLATION, _ERROR_LOCK_VIOLATION):
            error_type = (
                AuthorizationDomainAlreadyOwnedError
                if domain
                else AuthorizationDomainOwnershipUnavailableError
            )
            raise error_type("the ownership lock is already held") from error
        raise AuthorizationDomainOwnershipUnavailableError(
            "the ownership lock could not be opened"
        ) from error
    try:
        attributes = _file_attribute_info(handle)
        standard = _file_standard_info(handle)
        if (
            attributes.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT
            or standard.Directory
            or standard.NumberOfLinks != 1
        ):
            raise AuthorizationDomainOwnershipIntegrityError(
                "the ownership lock file is aliased or not regular"
            )
        _validate_security_profile(path, sid, directory=False)
        return handle
    except BaseException:
        handle.close()
        raise


class _LockedRegistry:
    __slots__ = ("root", "domain_directory", "sid", "domain_id", "key", "lock")

    def __init__(
        self,
        *,
        root: Path,
        domain_directory: Path,
        sid: str,
        domain_id: str,
        key: str,
        lock: _Handle,
    ) -> None:
        self.root = root
        self.domain_directory = domain_directory
        self.sid = sid
        self.domain_id = domain_id
        self.key = key
        self.lock = lock

    def close(self) -> None:
        self.lock.close()

    def __enter__(self) -> _LockedRegistry:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _validate_residue(self) -> None:
        try:
            entries = tuple(os.scandir(self.domain_directory))
        except OSError as error:
            raise AuthorizationDomainOwnershipUnavailableError(
                "the domain registry directory cannot be enumerated"
            ) from error
        names = {entry.name for entry in entries}
        if len(names) != len(entries) or not names.issubset(_DOMAIN_FILES):
            raise AuthorizationDomainOwnershipIntegrityError(
                "unexpected or duplicate domain-registry residue detected"
            )
        for entry in entries:
            if not entry.is_file(follow_symlinks=False) or entry.is_symlink():
                raise AuthorizationDomainOwnershipIntegrityError(
                    "domain registry contains a non-regular record"
                )

    def load(self, *, require_binding: bool = True) -> _RegistryState | None:
        self.lock.check_live()
        _reject_reparse_components(self.domain_directory, terminal_directory=True)
        _validate_security_profile(self.domain_directory, self.sid, directory=True)
        self._validate_residue()
        binding_path = self.domain_directory / _BINDING_FILE
        if not _record_exists(binding_path):
            if any(_record_exists(self.domain_directory / name) for name in (
                _ACTIVE_FILE,
                _FENCING_FILE,
                _FENCED_FILE,
            )):
                raise AuthorizationDomainOwnershipIntegrityError(
                    "state markers exist without an immutable binding"
                )
            if require_binding:
                raise AuthorizationDomainOwnershipStateError(
                    "the authorization domain is not registered"
                )
            return None
        binding_document = _decode_record(
            _read_registry_record(binding_path, self.sid),
            expected_keys=_BINDING_KEYS,
        )
        binding = _parse_binding(
            binding_document,
            authorization_domain_id=self.domain_id,
            sid=self.sid,
        )

        active_digest = None
        fencing_digest = None
        fenced_digest = None
        state = "inactive"
        active_path = self.domain_directory / _ACTIVE_FILE
        fencing_path = self.domain_directory / _FENCING_FILE
        fenced_path = self.domain_directory / _FENCED_FILE
        if _record_exists(active_path):
            active = _decode_record(
                _read_registry_record(active_path, self.sid),
                expected_keys=_MARKER_KEYS,
            )
            active_digest = _parse_marker(
                active,
                binding,
                state="active",
                predecessor_kind="binding",
                predecessor_sha256=binding.digest,
            )
            state = "active"
        if _record_exists(fencing_path):
            if active_digest is None:
                raise AuthorizationDomainOwnershipIntegrityError(
                    "fencing marker exists without active predecessor"
                )
            fencing = _decode_record(
                _read_registry_record(fencing_path, self.sid),
                expected_keys=_MARKER_KEYS,
            )
            fencing_digest = _parse_marker(
                fencing,
                binding,
                state="fencing",
                predecessor_kind="active",
                predecessor_sha256=active_digest,
            )
            state = "fencing"
        if _record_exists(fenced_path):
            if fencing_digest is None:
                raise AuthorizationDomainOwnershipIntegrityError(
                    "fenced marker exists without fencing predecessor"
                )
            fenced = _decode_record(
                _read_registry_record(fenced_path, self.sid),
                expected_keys=_MARKER_KEYS,
            )
            fenced_digest = _parse_marker(
                fenced,
                binding,
                state="fenced",
                predecessor_kind="fencing",
                predecessor_sha256=fencing_digest,
            )
            state = "fenced"
        return _RegistryState(
            binding=binding,
            state=state,
            active_digest=active_digest,
            fencing_digest=fencing_digest,
            fenced_digest=fenced_digest,
        )

    def publish_binding(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        file_identity: _WindowsFileIdentity,
    ) -> _LocalAuthorizationDomainBinding:
        if self.load(require_binding=False) is not None:
            raise AuthorizationDomainOwnershipStateError(
                "an immutable binding already exists; rebinding is unsupported"
            )
        data, _ = _encode_record(
            _binding_payload(configuration, self.sid, file_identity)
        )
        _publish_record(self.domain_directory / _BINDING_FILE, data, self.sid)
        state = self.load()
        assert state is not None
        if state.state != "inactive":
            raise AuthorizationDomainOwnershipIntegrityError(
                "new binding did not remain externally inactive"
            )
        return state.binding

    def publish_marker(self, state: str) -> _RegistryState:
        current = self.load()
        assert current is not None
        if state == "active":
            if current.state != "inactive":
                if current.state == "active":
                    return current
                raise AuthorizationDomainOwnershipStateError(
                    "terminal or fencing domains cannot be activated"
                )
            name = _ACTIVE_FILE
            predecessor_kind = "binding"
            predecessor_digest = current.binding.digest
        elif state == "fencing":
            if current.state == "fenced":
                return current
            if current.state == "fencing":
                return current
            if current.state != "active" or current.active_digest is None:
                raise AuthorizationDomainOwnershipStateError(
                    "only an active domain can begin fencing"
                )
            name = _FENCING_FILE
            predecessor_kind = "active"
            predecessor_digest = current.active_digest
        elif state == "fenced":
            if current.state == "fenced":
                return current
            if current.state != "fencing" or current.fencing_digest is None:
                raise AuthorizationDomainOwnershipStateError(
                    "fenced publication requires durable fencing evidence"
                )
            name = _FENCED_FILE
            predecessor_kind = "fencing"
            predecessor_digest = current.fencing_digest
        else:
            raise ValueError("state marker must be active, fencing, or fenced")
        data, _ = _encode_record(
            _marker_payload(
                current.binding,
                state=state,
                predecessor_kind=predecessor_kind,
                predecessor_sha256=predecessor_digest,
            )
        )
        _publish_record(self.domain_directory / name, data, self.sid)
        published = self.load()
        assert published is not None
        if published.state != state:
            raise AuthorizationDomainOwnershipIntegrityError(
                f"{state!r} marker did not become effective"
            )
        return published


def _lock_registry(
    authorization_domain_id: str,
    *,
    create_domain_directory: bool = True,
) -> _LockedRegistry:
    _require_windows()
    key = _domain_key(authorization_domain_id)
    sid = _current_user_sid()
    root = _create_registry_namespace(sid)
    bootstrap = _open_lock(root / _LOCKS_DIRECTORY / _BOOTSTRAP_LOCK, sid, domain=False)
    try:
        domain_directory = root / _DOMAINS_DIRECTORY / key
        if create_domain_directory:
            _create_secure_directory(domain_directory, sid)
        else:
            attributes = _win32()[0].GetFileAttributesW(str(domain_directory))
            if attributes == _INVALID_FILE_ATTRIBUTES:
                code = ctypes.get_last_error()
                if code in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
                    raise AuthorizationDomainOwnershipStateError(
                        "the authorization domain is not registered"
                    )
                raise AuthorizationDomainOwnershipUnavailableError(
                    f"the domain registry is unavailable: WinError {code}"
                )
            if (
                not attributes & _FILE_ATTRIBUTE_DIRECTORY
                or attributes & _FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise AuthorizationDomainOwnershipIntegrityError(
                    "the domain registry is aliased or not a directory"
                )
            _validate_security_profile(domain_directory, sid, directory=True)
    finally:
        bootstrap.close()
    lock = _open_lock(root / _LOCKS_DIRECTORY / f"{key}.lock", sid, domain=True)
    try:
        return _LockedRegistry(
            root=root,
            domain_directory=domain_directory,
            sid=sid,
            domain_id=authorization_domain_id,
            key=key,
            lock=lock,
        )
    except BaseException:
        lock.close()
        raise


def _configuration_from_binding(
    binding: _LocalAuthorizationDomainBinding,
    *,
    busy_timeout_ms: int,
) -> SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
    return SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
        database_path=_normal_path_from_final(binding.canonical_ledger_path),
        authorization_domain_id=binding.authorization_domain_id,
        ledger_instance_id=binding.ledger_instance_id,
        domain_generation=binding.domain_generation,
        busy_timeout_ms=busy_timeout_ms,
    )


def _identity_matches_binding(
    binding: _LocalAuthorizationDomainBinding,
    identity: _WindowsFileIdentity,
) -> bool:
    return (
        identity.canonical_final_path == binding.canonical_ledger_path
        and identity.volume_serial_number == binding.volume_serial_number
        and identity.file_id == binding.file_id
        and identity.link_count == binding.link_count == 1
    )


def _verify_binding_ledger(
    binding: _LocalAuthorizationDomainBinding,
    sid: str,
) -> tuple[_Handle, _WindowsFileIdentity]:
    path = _normal_path_from_final(binding.canonical_ledger_path)
    pin, identity = _open_ledger_pin(path, sid)
    if not _identity_matches_binding(binding, identity):
        pin.close()
        raise AuthorizationDomainOwnershipIntegrityError(
            "the registered ledger path or stable file identity changed"
        )
    return pin, identity


def _admin_result(
    outcome: AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    detail: str,
) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
    return make_agent_execution_dispatch_admission_store_administration_result(
        outcome,
        detail=detail,
    )


_FAULT_HOOK: Callable[[str], None] | None = None


def _fault(point: str) -> None:
    hook = _FAULT_HOOK
    if hook is not None:
        hook(point)


def _mint_operational_access(identity: AuthorizationDomainIdentity):
    return _mint_owned_agent_execution_dispatch_admission_store_access(
        identity.authorization_domain_id,
        identity.ledger_instance_id,
        identity.domain_generation,
    )


def _mint_administrative_access(identity: AuthorizationDomainIdentity):
    return _mint_owned_agent_execution_dispatch_admission_store_administration_access(
        identity.authorization_domain_id,
        identity.ledger_instance_id,
        identity.domain_generation,
    )


def _open_owned_store(
    binding: _LocalAuthorizationDomainBinding,
    *,
    clock: AgentExecutionDispatchAdmissionClock,
    busy_timeout_ms: int,
    administrative: bool,
    allow_fenced: bool,
) -> SqliteAgentExecutionDispatchAdmissionStore:
    configuration = _configuration_from_binding(
        binding,
        busy_timeout_ms=busy_timeout_ms,
    )
    access = (
        _mint_administrative_access(binding.identity)
        if administrative
        else _mint_operational_access(binding.identity)
    )
    return SqliteAgentExecutionDispatchAdmissionStore._open_for_ownership(
        configuration,
        clock=clock,
        access=access,
        allow_fenced=allow_fenced,
        administrative=administrative,
    )


def _verified_sqlite_state(
    store: SqliteAgentExecutionDispatchAdmissionStore,
) -> str:
    state = store._verified_activation_state_for_ownership()
    if state not in ("active", "fenced"):
        raise AuthorizationDomainOwnershipIntegrityError(
            "the exact SQLite ledger activation state is invalid"
        )
    return state


def _ensure_exact_configuration(
    configuration: object,
) -> SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
    if type(configuration) is not SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
        raise TypeError(
            "configuration must be the exact SQLite Admission-store type"
        )
    AuthorizationDomainIdentity(
        authorization_domain_id=configuration.authorization_domain_id,
        ledger_instance_id=configuration.ledger_instance_id,
        domain_generation=configuration.domain_generation,
    )
    if (
        not isinstance(configuration.database_path, Path)
        or not configuration.database_path.is_absolute()
        or type(configuration.busy_timeout_ms) is not int
        or configuration.busy_timeout_ms < 0
    ):
        raise ValueError("the administrative SQLite configuration is invalid")
    return configuration


class WindowsLocalAuthorizationDomainAdministration:
    """Trusted administrative entrypoint, separate from operational ownership.

    The class authenticates no Human or policy principal.  It is intended to
    be exposed only by trusted composition.  Every operation serializes on the
    same domain-keyed OS lock but holding that lock is only concurrency
    control, never proof of administrative entitlement.
    """

    __slots__ = ("_clock", "_busy_timeout_ms")

    def __init__(
        self,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        if not callable(getattr(clock, "now_utc", None)):
            raise TypeError("clock must implement now_utc()")
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a nonnegative exact integer")
        self._clock = clock
        self._busy_timeout_ms = busy_timeout_ms

    def provision(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    ) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
        """Provision one ledger under the domain lock with no implicit binding."""

        configuration = _ensure_exact_configuration(configuration)
        with _lock_registry(configuration.authorization_domain_id) as registry:
            if registry.load(require_binding=False) is not None:
                return _admin_result(
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    STORAGE_UNAVAILABLE,
                    "provisioning refuses a domain that is already bound",
                )
            try:
                attributes = _win32()[0].GetFileAttributesW(
                    str(configuration.database_path.parent)
                )
                if attributes == _INVALID_FILE_ATTRIBUTES:
                    code = ctypes.get_last_error()
                    if code not in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
                        raise AuthorizationDomainOwnershipUnavailableError(
                            f"ledger directory state is unavailable: WinError {code}"
                        )
                    _validate_local_ntfs_path(
                        configuration.database_path.parent.parent
                    )
                    _reject_reparse_components(
                        configuration.database_path.parent.parent,
                        terminal_directory=True,
                    )
                    _create_secure_directory(
                        configuration.database_path.parent,
                        registry.sid,
                    )
                _validate_local_ntfs_path(configuration.database_path.parent)
                _reject_reparse_components(
                    configuration.database_path.parent,
                    terminal_directory=True,
                )
                _validate_security_profile(
                    configuration.database_path.parent,
                    registry.sid,
                    directory=True,
                )
            except AuthorizationDomainOwnershipIntegrityError as error:
                return _admin_result(
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    INTEGRITY_FAILURE,
                    str(error),
                )
            except AuthorizationDomainOwnershipError as error:
                return _admin_result(
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    STORAGE_UNAVAILABLE,
                    str(error),
                )
            access = _mint_administrative_access(
                AuthorizationDomainIdentity(
                    configuration.authorization_domain_id,
                    configuration.ledger_instance_id,
                    configuration.domain_generation,
                )
            )
            result = SqliteAgentExecutionDispatchAdmissionStore.provision(
                configuration,
                access=access,
            )
            if (
                result.outcome
                is AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                PROVISIONED
            ):
                try:
                    _apply_security_profile(
                        configuration.database_path,
                        registry.sid,
                        directory=False,
                    )
                    pin, _ = _open_ledger_pin(
                        configuration.database_path,
                        registry.sid,
                    )
                    pin.close()
                except AuthorizationDomainOwnershipError as error:
                    return _admin_result(
                        AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                        INTEGRITY_FAILURE,
                        f"provisioned ledger security verification failed: {error}",
                    )
            return result

    def register(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    ) -> AuthorizationDomainIdentity:
        """Create one immutable inactive binding for an exact pristine ledger."""

        configuration = _ensure_exact_configuration(configuration)
        with _lock_registry(configuration.authorization_domain_id) as registry:
            if registry.load(require_binding=False) is not None:
                raise AuthorizationDomainOwnershipStateError(
                    "the domain is already registered and cannot be rebound"
                )
            pin, file_identity = _open_ledger_pin(
                configuration.database_path,
                registry.sid,
            )
            try:
                identity = AuthorizationDomainIdentity(
                    configuration.authorization_domain_id,
                    configuration.ledger_instance_id,
                    configuration.domain_generation,
                )
                access = _mint_administrative_access(identity)
                store = SqliteAgentExecutionDispatchAdmissionStore._open_for_ownership(
                    configuration,
                    clock=self._clock,
                    access=access,
                    allow_fenced=False,
                    administrative=True,
                )
                if _verified_sqlite_state(store) != "active":
                    raise AuthorizationDomainOwnershipStateError(
                        "only an internally active pristine ledger can be registered"
                    )
                if store.watermark() != (None, None):
                    raise AuthorizationDomainOwnershipIntegrityError(
                        "a ledger with Admission or revocation history is not pristine"
                    )
                binding = registry.publish_binding(configuration, file_identity)
                return binding.identity
            finally:
                pin.close()

    def activate(self, authorization_domain_id: str) -> AuthorizationDomainIdentity:
        """Explicitly activate one exact inactive binding after full revalidation."""

        with _lock_registry(authorization_domain_id) as registry:
            state = registry.load()
            assert state is not None
            if state.state == "active":
                return state.binding.identity
            if state.state != "inactive":
                raise AuthorizationDomainOwnershipStateError(
                    "fencing or fenced domains cannot be activated"
                )
            pin, _ = _verify_binding_ledger(state.binding, registry.sid)
            try:
                store = _open_owned_store(
                    state.binding,
                    clock=self._clock,
                    busy_timeout_ms=self._busy_timeout_ms,
                    administrative=True,
                    allow_fenced=False,
                )
                if _verified_sqlite_state(store) != "active":
                    raise AuthorizationDomainOwnershipStateError(
                        "the registered ledger is not internally active"
                    )
                if store.watermark() != (None, None):
                    raise AuthorizationDomainOwnershipIntegrityError(
                        "activation requires a pristine unused ledger"
                    )
                activated = registry.publish_marker("active")
                return activated.binding.identity
            finally:
                pin.close()

    def migrate(
        self,
        authorization_domain_id: str,
    ) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
        """Run explicit same-file migration under the exact domain lock."""

        with _lock_registry(authorization_domain_id) as registry:
            state = registry.load()
            assert state is not None
            if state.state in ("fencing", "fenced"):
                return _admin_result(
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    MIGRATION_FAILURE,
                    "terminal or fencing domains cannot be migrated",
                )
            pin, _ = _verify_binding_ledger(state.binding, registry.sid)
            try:
                configuration = _configuration_from_binding(
                    state.binding,
                    busy_timeout_ms=self._busy_timeout_ms,
                )
                result = SqliteAgentExecutionDispatchAdmissionStore.migrate(
                    configuration,
                    access=_mint_administrative_access(state.binding.identity),
                )
                if result.outcome in (
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    MIGRATED,
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    ALREADY_CURRENT,
                ):
                    _verify_binding_ledger(state.binding, registry.sid)[0].close()
                return result
            finally:
                pin.close()

    def create_fenced_backup(
        self,
        authorization_domain_id: str,
        destination: Path,
    ) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
        """Create one AIO-047-consistent, unbound, permanently fenced backup."""

        if not isinstance(destination, Path) or not destination.is_absolute():
            raise ValueError("destination must be an exact absolute pathlib.Path")
        with _lock_registry(authorization_domain_id) as registry:
            state = registry.load()
            assert state is not None
            if state.state != "active":
                return _admin_result(
                    AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    STORAGE_UNAVAILABLE,
                    "backup requires an externally active domain",
                )
            pin, _ = _verify_binding_ledger(state.binding, registry.sid)
            try:
                _validate_local_ntfs_path(destination.parent)
                _reject_reparse_components(
                    destination.parent,
                    terminal_directory=True,
                )
                _validate_security_profile(
                    destination.parent,
                    registry.sid,
                    directory=True,
                )
                store = _open_owned_store(
                    state.binding,
                    clock=self._clock,
                    busy_timeout_ms=self._busy_timeout_ms,
                    administrative=True,
                    allow_fenced=False,
                )
                result = store.create_fenced_backup(destination)
                if (
                    result.outcome
                    is AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    FENCED_BACKUP_CREATED
                ):
                    _apply_security_profile(
                        destination,
                        registry.sid,
                        directory=False,
                    )
                return result
            finally:
                pin.close()

    def fence(self, authorization_domain_id: str) -> None:
        """Begin and complete the irreversible fencing sequence."""

        with _lock_registry(authorization_domain_id) as registry:
            state = registry.load()
            assert state is not None
            if state.state == "inactive":
                raise AuthorizationDomainOwnershipStateError(
                    "an inactive domain cannot be fenced as an operational owner"
                )
            self._drive_fencing(registry, state, recovery=False)

    def recover_fencing(self, authorization_domain_id: str) -> None:
        """Reconcile only forward from durable terminal or fencing evidence."""

        with _lock_registry(authorization_domain_id) as registry:
            state = registry.load()
            assert state is not None
            if state.state == "inactive":
                raise AuthorizationDomainOwnershipStateError(
                    "inactive state has no forward fencing recovery"
                )
            self._drive_fencing(registry, state, recovery=True)

    def _drive_fencing(
        self,
        registry: _LockedRegistry,
        state: _RegistryState,
        *,
        recovery: bool,
        pinned: _Handle | None = None,
        store: SqliteAgentExecutionDispatchAdmissionStore | None = None,
    ) -> None:
        own_pin = pinned is None
        if pinned is None:
            pinned, _ = _verify_binding_ledger(state.binding, registry.sid)
        assert pinned is not None
        try:
            if store is None:
                store = _open_owned_store(
                    state.binding,
                    clock=self._clock,
                    busy_timeout_ms=self._busy_timeout_ms,
                    administrative=True,
                    allow_fenced=True,
                )
            sqlite_state = _verified_sqlite_state(store)
            if recovery and state.state == "active" and sqlite_state == "active":
                raise AuthorizationDomainOwnershipStateError(
                    "no durable fencing evidence exists to recover"
                )
            if state.state == "active":
                state = registry.publish_marker("fencing")
            elif state.state == "fencing":
                pass
            elif state.state == "fenced":
                pass
            else:
                raise AuthorizationDomainOwnershipStateError(
                    "fencing requires active, fencing, or fenced external state"
                )
            _fault("after_fencing_publish")
            if sqlite_state == "active":
                _fault("before_sqlite_fence")
                result = store.fence()
                if (
                    result.outcome
                    is AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    COMMIT_UNKNOWN
                ):
                    raise AuthorizationDomainOwnershipUnavailableError(
                        "SQLite fencing commit is unknown; explicit recovery is required"
                    )
                if (
                    result.outcome
                    is not AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
                    FENCED
                ):
                    raise AuthorizationDomainOwnershipIntegrityError(
                        f"SQLite fencing failed closed: {result.detail}"
                    )
            _fault("after_sqlite_fence")
            current = registry.load()
            assert current is not None
            if current.state == "fenced":
                return
            if current.state != "fencing":
                raise AuthorizationDomainOwnershipIntegrityError(
                    "external state changed incoherently during fencing"
                )
            _fault("before_fenced_publish")
            registry.publish_marker("fenced")
            _fault("after_fenced_publish")
        finally:
            if own_pin:
                pinned.close()


_SESSION_CREATION_AUTHORITY = object()


class _WindowsOwnedAuthorizationDomainOperation:
    __slots__ = ("_session", "_entered")

    def __init__(self, session: _WindowsOwnedAuthorizationDomainSession) -> None:
        self._session = session
        self._entered = False

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return self._session.identity

    def __enter__(self) -> _WindowsOwnedAuthorizationDomainOperation:
        if self._entered:
            raise AuthorizationDomainOwnershipStateError(
                "an ownership operation lease is single-use"
            )
        self._session._begin_operation()
        self._entered = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if not self._entered:
            return False
        self._entered = False
        self._session._finish_operation(revalidate=True)
        return False

    def __copy__(self):
        raise TypeError("ownership operation leases cannot be copied")

    def __deepcopy__(self, memo):
        del memo
        raise TypeError("ownership operation leases cannot be deep-copied")

    def __reduce__(self):
        raise TypeError("ownership operation leases cannot be serialized")


class _WindowsOwnedAuthorizationDomainSession(OwnedAuthorizationDomainSession):
    __slots__ = (
        "_identity",
        "_binding",
        "_registry",
        "_pin",
        "_store",
        "_coordinator",
        "_administration",
        "_condition",
        "_state",
        "_operations",
        "_thread_operations",
    )

    def __new__(cls, *args, **kwargs):
        authority = kwargs.pop("_creation_authority", None)
        if authority is not _SESSION_CREATION_AUTHORITY or args or kwargs:
            raise TypeError(
                "Owned Authorization Domain Sessions are adapter-created"
            )
        return super().__new__(cls)

    @classmethod
    def _create(
        cls,
        *,
        binding: _LocalAuthorizationDomainBinding,
        registry: _LockedRegistry,
        pin: _Handle,
        store: SqliteAgentExecutionDispatchAdmissionStore,
        coordinator: AgentExecutionDispatchAdmissionCoordinator,
        administration: WindowsLocalAuthorizationDomainAdministration,
    ) -> _WindowsOwnedAuthorizationDomainSession:
        self = cls(_creation_authority=_SESSION_CREATION_AUTHORITY)
        self._identity = binding.identity
        self._binding = binding
        self._registry = registry
        self._pin = pin
        self._store = store
        self._coordinator = coordinator
        self._administration = administration
        self._condition = threading.Condition(threading.RLock())
        self._state = "live"
        self._operations = 0
        self._thread_operations: dict[int, int] = {}
        return self

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return self._identity

    def operation(self) -> _WindowsOwnedAuthorizationDomainOperation:
        return _WindowsOwnedAuthorizationDomainOperation(self)

    def _revalidate(self) -> None:
        self._registry.lock.check_live()
        self._pin.check_live()
        state = self._registry.load()
        if (
            state is None
            or state.state != "active"
            or state.binding != self._binding
        ):
            raise AuthorizationDomainOwnershipIntegrityError(
                "the exact active external binding no longer agrees"
            )
        identity = _identity_from_handle(self._pin)
        if not _identity_matches_binding(self._binding, identity):
            raise AuthorizationDomainOwnershipIntegrityError(
                "the pinned ledger identity no longer agrees"
            )
        _validate_ledger_storage_security(
            _normal_path_from_final(self._binding.canonical_ledger_path),
            self._registry.sid,
        )
        if _verified_sqlite_state(self._store) != "active":
            raise AuthorizationDomainOwnershipStateError(
                "the owned SQLite ledger is no longer active"
            )

    def _begin_operation(self) -> None:
        thread_id = threading.get_ident()
        with self._condition:
            if self._state == "lost":
                raise OwnedAuthorizationDomainSessionLostError(
                    "the ownership session irreversibly lost authority"
                )
            if self._state != "live":
                raise OwnedAuthorizationDomainSessionClosedError(
                    "the ownership session is closed or terminally transitioning"
                )
            self._operations += 1
            self._thread_operations[thread_id] = (
                self._thread_operations.get(thread_id, 0) + 1
            )
        try:
            self._revalidate()
        except BaseException:
            self._finish_operation(revalidate=False, lost=True)
            raise

    def _finish_operation(
        self,
        *,
        revalidate: bool,
        lost: bool = False,
    ) -> None:
        failure: BaseException | None = None
        if revalidate:
            try:
                self._revalidate()
            except BaseException as error:
                lost = True
                failure = error
        thread_id = threading.get_ident()
        close_now = False
        with self._condition:
            count = self._thread_operations.get(thread_id, 0)
            if count <= 1:
                self._thread_operations.pop(thread_id, None)
            else:
                self._thread_operations[thread_id] = count - 1
            self._operations -= 1
            if lost and self._state == "live":
                self._state = "lost"
            close_now = self._operations == 0 and self._state == "lost"
            self._condition.notify_all()
        if close_now:
            self._release_handles()
        if failure is not None:
            raise AuthorizationDomainOwnershipIntegrityError(
                "ownership revalidation failed after the complete operation"
            ) from failure

    def _operation_failure_result(self, error: BaseException):
        outcome = (
            AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE
            if isinstance(error, AuthorizationDomainOwnershipIntegrityError)
            else AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE
        )
        return make_agent_execution_dispatch_admission_store_result(
            outcome,
            detail=f"owned authorization-domain session failed closed: {error}",
        )

    def _run(self, method_name: str, presented_grant: object):
        try:
            with self.operation():
                return getattr(self._coordinator, method_name)(presented_grant)
        except Exception as error:
            if isinstance(error, AuthorizationDomainOwnershipError):
                return self._operation_failure_result(error)
            return self._operation_failure_result(
                AuthorizationDomainOwnershipUnavailableError(
                    "the complete owned coordinator operation was unavailable"
                )
            )

    def admit(self, presented_grant: object):
        return self._run("admit", presented_grant)

    def load_authoritative_admission(self, presented_grant: object):
        return self._run("load_authoritative_admission", presented_grant)

    def revoke(self, presented_grant: object):
        return self._run("revoke", presented_grant)

    def _quiesce(self, target_state: str) -> None:
        thread_id = threading.get_ident()
        with self._condition:
            if self._thread_operations.get(thread_id, 0):
                raise AuthorizationDomainOwnershipStateError(
                    "a session cannot close or fence from its own operation lease"
                )
            if self._state == "closed":
                return
            if self._state != "live":
                if self._state == "lost":
                    raise OwnedAuthorizationDomainSessionLostError(
                        "the ownership session irreversibly lost authority"
                    )
                raise OwnedAuthorizationDomainSessionClosedError(
                    "the ownership session is already closing or fenced"
                )
            self._state = target_state
            while self._operations:
                self._condition.wait()

    def _release_handles(self) -> None:
        errors: list[BaseException] = []
        for resource in (self._pin, self._registry):
            try:
                resource.close()
            except BaseException as error:
                errors.append(error)
        if errors:
            raise AuthorizationDomainOwnershipUnavailableError(
                "one or more ownership handles could not be released"
            ) from errors[0]

    def close(self) -> None:
        with self._condition:
            if self._state == "closed":
                return
            if self._state == "lost":
                while self._operations:
                    self._condition.wait()
                try:
                    self._release_handles()
                finally:
                    self._state = "closed"
                    self._condition.notify_all()
                return
        self._quiesce("closing")
        try:
            self._release_handles()
        finally:
            with self._condition:
                self._state = "closed"
                self._condition.notify_all()

    def fence(self) -> None:
        self._quiesce("fencing")
        try:
            state = self._registry.load()
            assert state is not None
            if state.binding != self._binding:
                raise AuthorizationDomainOwnershipIntegrityError(
                    "the exact binding changed before fencing"
                )
            self._administration._drive_fencing(
                self._registry,
                state,
                recovery=False,
                pinned=self._pin,
                store=self._store,
            )
        except BaseException as error:
            with self._condition:
                self._state = "lost"
            try:
                self._release_handles()
            except BaseException:
                pass
            if isinstance(error, AuthorizationDomainOwnershipError):
                raise
            raise AuthorizationDomainOwnershipUnavailableError(
                "terminal fencing failed or became ambiguous"
            ) from error
        else:
            try:
                self._release_handles()
            finally:
                with self._condition:
                    self._state = "closed"
                    self._condition.notify_all()


class WindowsLocalAuthorizationDomainOwner:
    """Acquire live ownership for one fixed-registry authorization domain."""

    __slots__ = (
        "_clock",
        "_busy_timeout_ms",
        "_grant_authentication",
        "_tool_binding_resolver",
        "_fresh_prerequisite_source",
        "_execution_mode_resolver",
        "_revocation_authentication",
        "_administration",
    )

    def __init__(
        self,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
        grant_authentication: AgentExecutionAuthorizationGrantAuthenticationPort,
        tool_binding_resolver: AgentOperationToolBindingResolverPort,
        fresh_prerequisite_source: FreshAgentActionPrerequisiteSourcePort,
        execution_mode_resolver: EffectiveExecutionModeResolverPort,
        revocation_authentication: OriginalIssuerRevocationAuthenticationPort,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        if not callable(getattr(clock, "now_utc", None)):
            raise TypeError("clock must implement now_utc()")
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a nonnegative exact integer")
        self._clock = clock
        self._busy_timeout_ms = busy_timeout_ms
        self._grant_authentication = grant_authentication
        self._tool_binding_resolver = tool_binding_resolver
        self._fresh_prerequisite_source = fresh_prerequisite_source
        self._execution_mode_resolver = execution_mode_resolver
        self._revocation_authentication = revocation_authentication
        self._administration = WindowsLocalAuthorizationDomainAdministration(
            clock=clock,
            busy_timeout_ms=busy_timeout_ms,
        )

    def acquire(
        self,
        authorization_domain_id: str,
    ) -> OwnedAuthorizationDomainSession:
        """Acquire by domain ID only and return one live nonserializable session."""

        registry = _lock_registry(
            authorization_domain_id,
            create_domain_directory=False,
        )
        pin: _Handle | None = None
        try:
            state = registry.load()
            assert state is not None
            if state.state != "active":
                raise AuthorizationDomainOwnershipStateError(
                    "operational acquisition requires exact external active state"
                )
            pin, _ = _verify_binding_ledger(state.binding, registry.sid)
            store = _open_owned_store(
                state.binding,
                clock=self._clock,
                busy_timeout_ms=self._busy_timeout_ms,
                administrative=False,
                allow_fenced=False,
            )
            if _verified_sqlite_state(store) != "active":
                raise AuthorizationDomainOwnershipStateError(
                    "operational acquisition requires exact SQLite active state"
                )
            coordinator = AgentExecutionDispatchAdmissionCoordinator(
                authorization_domain_id=authorization_domain_id,
                store=store,
                grant_authentication=self._grant_authentication,
                tool_binding_resolver=self._tool_binding_resolver,
                fresh_prerequisite_source=self._fresh_prerequisite_source,
                execution_mode_resolver=self._execution_mode_resolver,
                revocation_authentication=self._revocation_authentication,
            )
            session = _WindowsOwnedAuthorizationDomainSession._create(
                binding=state.binding,
                registry=registry,
                pin=pin,
                store=store,
                coordinator=coordinator,
                administration=self._administration,
            )
            session._revalidate()
            pin = None
            registry = None  # type: ignore[assignment]
            return session
        except BaseException:
            if pin is not None:
                pin.close()
            if registry is not None:
                registry.close()
            raise
