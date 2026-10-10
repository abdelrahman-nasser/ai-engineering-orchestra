"""NONCANONICAL containment experiment; import performs no native or file IO.

Retained RootDirectory NtCreateFile is the sole reader strategy. Pathname
operations and diskpart are disposable fixture control, never reader fallback.
"""
from __future__ import annotations
import ctypes as C
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import threading
import sys
import time
import uuid

TEMP_PARENT = Path(r'C:\Users\Abdelrahman\AppData\Local\Temp')
SYSTEM32 = r'C:\Windows\System32'
MAX_BYTES, MAX_PHYSICAL_BYTES, MAX_DATA_REQUESTS = 65536, 65537, 17
MAX_COMPONENTS, MAX_RESOURCE_UNITS, OBSERVATION_SECONDS = 16, 4096, 5.0
CUTS = ('before_component_open', 'after_ancestor_pin', 'after_final_open_before_metadata', 'before_first_content_read')
FILE_READ_DATA, FILE_WRITE_DATA, FILE_READ_ATTRIBUTES, FILE_WRITE_ATTRIBUTES = 1, 2, 0x80, 0x100
DELETE, SYNCHRONIZE, SHARE_READ, SHARE_ALL = 0x10000, 0x100000, 1, 7
FILE_ATTRIBUTE_REPARSE_POINT, FILE_ATTRIBUTE_DEVICE = 0x400, 0x40
MOUNT_POINT_TAG, CUSTOM_TAG = 0xA0000003, 0x42
CUSTOM_GUID = uuid.UUID('05805858-0058-4058-8058-005800580058')
OUTSIDE_BYTES = b'AIO-058 synthetic outside sentinel'
ULONG, USHORT, HANDLE, NTSTATUS = C.c_uint32, C.c_uint16, C.c_void_p, C.c_int32
_UNVERIFIED_IO_BUFFERS = []

class Reject(Exception):
    """Closed rejection category, never fixture content or arbitrary paths."""

class UnverifiedNativeCompletion(BaseException):
    """Fatal unsupported experiment ABI; never a normal reader outcome."""

class NativeError(OSError):
    def __init__(self, operation, status, winerror):
        super().__init__(winerror, operation)
        self.operation, self.status, self.winerror = operation, status & 0xffffffff, winerror

def validate_resource(resource):
    if not isinstance(resource, str) or not resource or resource.startswith('/'):
        raise Reject('resource_unsupported')
    try:
        units = len(resource.encode('utf-16-le', errors='strict')) // 2
    except UnicodeError:
        raise Reject('resource_unsupported') from None
    pieces = tuple(resource.split('/'))
    if units > MAX_RESOURCE_UNITS or len(pieces) > MAX_COMPONENTS:
        raise Reject('resource_bound')
    for piece in pieces:
        if (not piece or piece in ('.', '..') or piece.endswith(('.', ' '))
                or any(ord(c) < 32 or c in '\\:<>"|?*' for c in piece)):
            raise Reject('resource_unsupported')
        stem = piece.split('.', 1)[0].upper()
        if stem in {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} or re.fullmatch(r'(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]', stem):
            raise Reject('resource_unsupported')
    return pieces

class UNICODE_STRING(C.Structure):
    _fields_ = [('Length', USHORT), ('MaximumLength', USHORT), ('Buffer', C.c_void_p)]
class OBJECT_ATTRIBUTES(C.Structure):
    _fields_ = [('Length', ULONG), ('RootDirectory', HANDLE), ('ObjectName', C.POINTER(UNICODE_STRING)),
                ('Attributes', ULONG), ('SecurityDescriptor', C.c_void_p), ('SecurityQualityOfService', C.c_void_p)]
class IOS_UNION(C.Union):
    _fields_ = [('Status', NTSTATUS), ('Pointer', C.c_void_p)]
class IO_STATUS_BLOCK(C.Structure):
    _anonymous_ = ('u',)
    _fields_ = [('u', IOS_UNION), ('Information', C.c_size_t)]
class FILE_STANDARD_INFO(C.Structure):
    _fields_ = [('AllocationSize', C.c_int64), ('EndOfFile', C.c_int64), ('NumberOfLinks', ULONG),
                ('DeletePending', C.c_ubyte), ('Directory', C.c_ubyte)]
class FILE_BASIC_INFO(C.Structure):
    _fields_ = [('CreationTime', C.c_int64), ('LastAccessTime', C.c_int64), ('LastWriteTime', C.c_int64),
                ('ChangeTime', C.c_int64), ('FileAttributes', ULONG)]
class FILE_ID_INFO(C.Structure):
    _fields_ = [('VolumeSerialNumber', C.c_uint64), ('FileId', C.c_ubyte * 16)]
class FILE_ATTRIBUTE_TAG_INFO(C.Structure):
    _fields_ = [('FileAttributes', ULONG), ('ReparseTag', ULONG)]

@dataclass(frozen=True)
class FileMetadata:
    identity: tuple[int, bytes]
    path: str
    size: int
    nlink: int
    directory: bool
    delete_pending: bool
    attributes: int
    tag: int
    file_type: int
    write_time: int
    change_time: int
    case_sensitive: bool = False

@dataclass(frozen=True)
class ProbeResult:
    accepted: bool
    reason: str
    data: bytes | None
    identity: tuple[int, bytes] | None
    opens: int
    metadata_queries: int
    data_requests: int
    physical_bytes: int
    native_calls: int
    retained_peak: int
    seconds: float
    handles_before: int
    handles_after: int
    trace: tuple[dict, ...]
    unauthorized_reads: int = 0
    fault_hit: bool = False
    metadata_per_handle: tuple[int, ...] = ()
    native_maxcall_seconds: float = 0.0
    @property
    def elapsed(self):
        return self.seconds
    @property
    def leak_free(self):
        return self.handles_before == self.handles_after

class Handle:
    def __init__(self, native, value, fixture_control=False, reader_profile=None):
        self.native, self.value = native, value
        self.fixture_control, self.reader_profile = fixture_control, reader_profile
        native._handles.add(self)
    def close(self):
        if self.value:
            self.native._invoke('CloseHandle', self.native.kernel.CloseHandle, HANDLE(self.value),
                                boolean=True, fixture_control=self.fixture_control)
            self.value = None
            self.native._handles.discard(self)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()

class Native:
    """Exact 64-bit Windows ABI with explicitly named System32 DLLs."""
    def __init__(self):
        if os.name != 'nt' or C.sizeof(C.c_void_p) != 8:
            raise Reject('unsupported_windows_abi')
        self.kernel = C.WinDLL(SYSTEM32 + r'\kernel32.dll', use_last_error=True)
        self.ntdll = C.WinDLL(SYSTEM32 + r'\ntdll.dll', use_last_error=True)
        self._handles, self.forbidden_ids, self._attempt = set(), set(), None
        self._views = set()
        self.views_created = self.views_unmapped = 0
        self.pending_completion_unverified = False
        self.children_created = self.children_reaped = 0
        self.roots_created, self.roots_cleaned = [], []
        self._bind()
        self.prerequisites = {'windows': str(sys.getwindowsversion()), 'abi': 'Windows x64',
                              'native_libraries': ['System32/kernel32.dll', 'System32/ntdll.dll'],
                              'privilege_changes': False, 'production_requires_admin': False,
                              'production_requires_developer_mode': False}
    @property
    def handle_count(self):
        return len(self._handles)
    @property
    def view_count(self):
        return len(self._views)
    def _active_attempt(self):
        state = self._attempt
        return state if state is not None and state['thread'] == threading.get_ident() else None
    def _bind(self):
        specs = {
            'CloseHandle': ([HANDLE], C.c_int),
            'CreateFileW': ([C.c_wchar_p, ULONG, ULONG, C.c_void_p, ULONG, ULONG, HANDLE], HANDLE),
            'CreateFileMappingW': ([HANDLE, C.c_void_p, ULONG, ULONG, ULONG, C.c_wchar_p], HANDLE),
            'MapViewOfFile': ([HANDLE, ULONG, ULONG, ULONG, C.c_size_t], C.c_void_p),
            'UnmapViewOfFile': ([C.c_void_p], C.c_int),
            'GetFileInformationByHandleEx': ([HANDLE, C.c_int, C.c_void_p, ULONG], C.c_int),
            'SetFileInformationByHandle': ([HANDLE, C.c_int, C.c_void_p, ULONG], C.c_int),
            'GetFileType': ([HANDLE], ULONG),
            'GetFinalPathNameByHandleW': ([HANDLE, C.c_wchar_p, ULONG, ULONG], ULONG),
            'GetVolumeInformationW': ([C.c_wchar_p, C.c_wchar_p, ULONG, C.POINTER(ULONG), C.POINTER(ULONG), C.POINTER(ULONG), C.c_wchar_p, ULONG], C.c_int),
            'GetVolumeInformationByHandleW': ([HANDLE, C.c_wchar_p, ULONG, C.POINTER(ULONG), C.POINTER(ULONG), C.POINTER(ULONG), C.c_wchar_p, ULONG], C.c_int),
            'GetDriveTypeW': ([C.c_wchar_p], ULONG),
            'DeviceIoControl': ([HANDLE, ULONG, C.c_void_p, ULONG, C.c_void_p, ULONG, C.POINTER(ULONG), C.c_void_p], C.c_int),
            'SetFileShortNameW': ([HANDLE, C.c_wchar_p], C.c_int),
            'GetShortPathNameW': ([C.c_wchar_p, C.c_wchar_p, ULONG], ULONG),
            'SetFilePointerEx': ([HANDLE, C.c_int64, C.POINTER(C.c_int64), ULONG], C.c_int),
            'SetEndOfFile': ([HANDLE], C.c_int),
            'WriteFile': ([HANDLE, C.c_void_p, ULONG, C.POINTER(ULONG), C.c_void_p], C.c_int),
            'DeleteVolumeMountPointW': ([C.c_wchar_p], C.c_int),
        }
        for name, (args, result) in specs.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result
        self.ntdll.NtCreateFile.argtypes = [C.POINTER(HANDLE), ULONG, C.POINTER(OBJECT_ATTRIBUTES), C.POINTER(IO_STATUS_BLOCK), C.POINTER(C.c_int64), ULONG, ULONG, ULONG, ULONG, C.c_void_p, ULONG]
        self.ntdll.NtCreateFile.restype = NTSTATUS
        self.ntdll.NtReadFile.argtypes = [HANDLE, HANDLE, C.c_void_p, C.c_void_p, C.POINTER(IO_STATUS_BLOCK), C.c_void_p, ULONG, C.POINTER(C.c_int64), C.POINTER(ULONG)]
        self.ntdll.NtReadFile.restype = NTSTATUS
        self.ntdll.NtSetInformationFile.argtypes = [HANDLE, C.POINTER(IO_STATUS_BLOCK), C.c_void_p, ULONG, C.c_int]
        self.ntdll.NtSetInformationFile.restype = NTSTATUS
        self.ntdll.NtWaitForSingleObject.argtypes = [HANDLE, C.c_ubyte, C.POINTER(C.c_int64)]
        self.ntdll.NtWaitForSingleObject.restype = NTSTATUS
        self.ntdll.RtlNtStatusToDosError.argtypes, self.ntdll.RtlNtStatusToDosError.restype = [NTSTATUS], ULONG
        if (C.sizeof(OBJECT_ATTRIBUTES) != 48 or C.sizeof(IO_STATUS_BLOCK) != 16
                or C.sizeof(FILE_STANDARD_INFO) != 24 or C.sizeof(FILE_BASIC_INFO) != 40 or C.sizeof(FILE_ID_INFO) != 24):
            raise Reject('unsupported_windows_abi')
    def _invoke(self, name, function, *args, boolean=False, nt=False, fixture_control=False):
        # Revised I14 setup/challenges are explicit fixture control. They do
        # not consume a reader call budget or trigger its fault injection.
        attempt = None if fixture_control else self._active_attempt()
        start = time.monotonic()
        if attempt is not None:
            attempt['native_calls'] += 1
            if attempt['native_calls'] > 253:
                raise Reject('native_call_bound')
            if attempt['fault'] == 'native_error' and name == 'NtCreateFile':
                attempt['fault_hit'] = True
                raise NativeError(name, 0xc0000001, 31)
            if attempt['fault'] == 'delay' and not attempt['delayed']:
                attempt['delayed'] = True
                attempt['fault_hit'] = True
                time.sleep(OBSERVATION_SECONDS + .05)
        try:
            result = function(*args)
        finally:
            elapsed = time.monotonic() - start
            if attempt is not None:
                attempt['trace'].append({'api': name, 'seconds': elapsed})
                attempt['native_maxcall_seconds'] = max(attempt['native_maxcall_seconds'], elapsed)
                if elapsed > OBSERVATION_SECONDS:
                    # Caller owns/releases any newly acquired handle first.
                    attempt['slow'] = True
        if nt and result < 0:
            code = self._invoke('RtlNtStatusToDosError', self.ntdll.RtlNtStatusToDosError, result,
                                fixture_control=fixture_control)
            raise NativeError(name, result, code)
        if boolean and not result:
            raise NativeError(name, 0, C.get_last_error())
        return result
    def _nt_open(self, component, parent=None, directory=False):
        encoded = component.encode('utf-16-le', errors='strict')
        if len(encoded) > 16382:
            raise Reject('native_name_buffer')
        buffer = C.create_string_buffer(encoded + b'\0\0')
        name = UNICODE_STRING(len(encoded), len(encoded) + 2, C.cast(buffer, C.c_void_p))
        # OBJ_DONT_REPARSE; OBJ_CASE_INSENSITIVE is deliberately absent.
        # The single trusted DOS drive-anchor bootstrap must resolve the C:
        # object-manager device map. Every filesystem component is relative
        # and uses OBJ_DONT_REPARSE. No resource may reach this bootstrap.
        attributes = OBJECT_ATTRIBUTES(C.sizeof(OBJECT_ATTRIBUTES), HANDLE(parent.value) if parent else None, C.pointer(name), 0x1000 if parent else 0, None, None)
        output, ios = HANDLE(), IO_STATUS_BLOCK()
        options = 0x00200000 | 0x20 | (1 if directory else 0x40)
        access = FILE_READ_ATTRIBUTES | SYNCHRONIZE | (0x20 if directory else FILE_READ_DATA)
        try:
            status = self._invoke('NtCreateFile', self.ntdll.NtCreateFile, C.byref(output), access, C.byref(attributes), C.byref(ios), None, 0, SHARE_READ, 1, options, None, 0, nt=True)
        except NativeError as error:
            state = self._active_attempt()
            if state is not None:
                state['trace'].append(dict(event='component_open_rejected', operation=error.operation,
                                           component_index=state['component_index'], directory=directory,
                                           desired_access=access, share_mode=SHARE_READ, create_options=options,
                                           object_attributes=attributes.Attributes, parent_relative=parent is not None,
                                           native_status=error.status, winerror=error.winerror))
            if state is not None and attributes.Attributes & 0x1000 and error.status == 0xc000050b:
                # This documented OBJ_DONT_REPARSE result proves the native
                # security guard ran; unrelated open errors prove nothing.
                state['trace'].append(dict(event='reparse_security_check', source='OBJ_DONT_REPARSE',
                                           component_index=state['component_index'], directory=directory,
                                           native_status=error.status, object_attributes=attributes.Attributes,
                                           create_options=options, parent_relative=parent is not None,
                                           rejected=True))
            raise
        if not output.value:
            raise Reject('malformed_native_handle')
        profile = dict(desired_access=access, share_mode=SHARE_READ, create_options=options,
                       object_attributes=attributes.Attributes, parent_relative=parent is not None)
        handle = Handle(self, output.value, reader_profile=profile)
        if status != 0:
            try:
                if status == 0x103:
                    self._drain_pending(handle, (buffer, name, attributes, ios, output))
            finally:
                handle.close()
            raise Reject('unsupported_native_completion')
        return handle
    def _drain_pending(self, handle, keepalive=()):
        # FILE_SYNCHRONOUS_IO_NONALERT should never expose pending IO. If an
        # environment violates that profile, retain buffers and this sole-use
        # handle until actual completion, then reject the support profile.
        retained = (handle, keepalive)
        _UNVERIFIED_IO_BUFFERS.append(retained)
        try:
            status = self._invoke('NtWaitForSingleObject', self.ntdll.NtWaitForSingleObject,
                                  HANDLE(handle.value), False, None)
        except BaseException:
            self.pending_completion_unverified = True
            self.prerequisites['pending_completion_unverified'] = True
            raise UnverifiedNativeCompletion('pending_completion_unverified') from None
        if status != 0:
            # Preserve native buffers through process teardown and STOP the
            # entire experiment; no successful/rejected return claims that an
            # unverified pending operation completed. No retry/poll loop.
            self.pending_completion_unverified = True
            self.prerequisites['pending_completion_unverified'] = True
            raise UnverifiedNativeCompletion('pending_completion_unverified')
        _UNVERIFIED_IO_BUFFERS.remove(retained)
    def control_open(self, path, access=FILE_READ_ATTRIBUTES, share=SHARE_ALL, directory=False, nofollow=True):
        # Disposable fixture control; read() never calls this pathname helper.
        flags = 0x02000000 | (0x00200000 if nofollow else 0)
        value = self._invoke('CreateFileW', self.kernel.CreateFileW, str(path), access, share, None, 3, flags, None)
        if value == C.c_void_p(-1).value or value is None:
            raise NativeError('CreateFileW', 0, C.get_last_error())
        return Handle(self, value)
    def _mapped_fixture_path(self, path):
        path = Path(path)
        exact = str(path)
        if not path.is_absolute() or not any(
                exact == root + '\\repo\\fixtures\\mapped.bin'
                and root not in self.roots_cleaned for root in self.roots_created):
            raise Reject('mapping_fixture_path_unsupported')
        return path
    def fixture_writer_open(self, path):
        path = self._mapped_fixture_path(path)
        value = self._invoke('CreateFileW', self.kernel.CreateFileW, str(path),
                             0xc0000000, SHARE_ALL, None, 3, 0x00200000, None,
                             fixture_control=True)
        if value == C.c_void_p(-1).value or value is None:
            raise NativeError('CreateFileW', 0, C.get_last_error())
        return Handle(self, value, fixture_control=True)
    def fixture_writable_state(self, path, expected_identity, kind='view'):
        return WritableState(self, self._mapped_fixture_path(path), expected_identity, kind)
    def _fixture_section(self, source):
        if source.native is not self or not source.value or source not in self._handles:
            raise Reject('mapping_source_not_live')
        value = self._invoke('CreateFileMappingW', self.kernel.CreateFileMappingW,
                             HANDLE(source.value), None, 4, 0, 4096, None,
                             fixture_control=True)
        if not value:
            raise NativeError('CreateFileMappingW', 0, C.get_last_error())
        return Handle(self, value, fixture_control=True)
    def _fixture_view(self, section):
        if section.native is not self or not section.value or section not in self._handles:
            raise Reject('mapping_section_not_live')
        address = self._invoke('MapViewOfFile', self.kernel.MapViewOfFile,
                               HANDLE(section.value), 2, 0, 0, 4096,
                               fixture_control=True)
        if not address:
            raise NativeError('MapViewOfFile', 0, C.get_last_error())
        return OwnedView(self, address, 4096)
    def fixture_readonly_mapping_attempt(self, reader_handle):
        self._require_target_live(reader_handle)
        value = self._invoke('CreateFileMappingW', self.kernel.CreateFileMappingW,
                             HANDLE(reader_handle.value), None, 4, 0, 4096, None,
                             fixture_control=True)
        evidence = dict(operation='CreateFileMappingW', protection=4,
                        succeeded=bool(value), winerror=0 if value else C.get_last_error())
        if value:
            # Unexpected success still owns and verifies release of the
            # section. The caller records proof failure, never a skipped check.
            with Handle(self, value, fixture_control=True):
                pass
        return evidence
    def _metadata_call(self, handle, name, function, *args, boolean=False):
        state = self._active_attempt()
        if state is not None:
            state['metadata_queries'] += 1
            count = state['queries_by_handle'].get(handle.value, 0) + 1
            state['queries_by_handle'][handle.value] = count
            if count > 12:
                raise Reject('metadata_bound')
        return self._invoke(name, function, *args, boolean=boolean)
    def _info(self, handle, kind, structure):
        value = structure()
        ok = self._metadata_call(handle, 'GetFileInformationByHandleEx', self.kernel.GetFileInformationByHandleEx, HANDLE(handle.value), kind, C.byref(value), C.sizeof(value))
        state = self._active_attempt()
        injected = state is not None and state.get('fault_query_handle') == handle.value
        if injected:
            state['fault_hit'] = True
            ok = False
        if not ok:
            raise NativeError('GetFileInformationByHandleEx', 0, 87 if injected else C.get_last_error())
        return value
    def metadata(self, handle, directory=False):
        standard, basic = self._info(handle, 1, FILE_STANDARD_INFO), self._info(handle, 0, FILE_BASIC_INFO)
        identity, tag = self._info(handle, 18, FILE_ID_INFO), self._info(handle, 9, FILE_ATTRIBUTE_TAG_INFO)
        file_type = self._metadata_call(handle, 'GetFileType', self.kernel.GetFileType, HANDLE(handle.value))
        path = C.create_unicode_buffer(8192)
        length = self._metadata_call(handle, 'GetFinalPathNameByHandleW', self.kernel.GetFinalPathNameByHandleW, HANDLE(handle.value), path, len(path), 0)
        if not length or length >= len(path):
            raise Reject('native_name_buffer')
        sensitive = bool(self._info(handle, 23, ULONG).value & 1) if directory else False
        if (standard.EndOfFile < 0 or standard.AllocationSize < 0 or tag.FileAttributes != basic.FileAttributes
                or bool(standard.Directory) != bool(basic.FileAttributes & 0x10)):
            raise Reject('malformed_metadata')
        return FileMetadata((identity.VolumeSerialNumber, bytes(identity.FileId)), path.value, standard.EndOfFile,
                            standard.NumberOfLinks, bool(standard.Directory), bool(standard.DeletePending),
                            basic.FileAttributes, tag.ReparseTag, file_type, basic.LastWriteTime, basic.ChangeTime, sensitive)
    def identity(self, path):
        with self.control_open(path) as handle:
            return self.metadata(handle).identity
    def pin_root(self, path):
        return RootCapability(self, Path(path))
    def read(self, cap, resource, expected_identity=None, hook=None, fault=None):
        if not isinstance(cap, RootCapability) or cap.native is not self or cap.closed:
            raise Reject('root_unavailable')
        if self._attempt is not None:
            raise Reject('reader_reentrancy')
        before, start = self.handle_count, time.monotonic()
        state = dict(opens=0, metadata_queries=0, data_requests=0, physical_bytes=0, native_calls=0,
                     peak=len(cap.handles), trace=[], queries_by_handle={}, fault=fault, delayed=False,
                     unauthorized_reads=0, thread=threading.get_ident(), slow=False,
                     fault_hit=False, native_maxcall_seconds=0.0, target_handle=None,
                     target_handle_token=1, target_verified=False, protection_live=False,
                     target_identity=None)
        self._attempt = state
        owned, output, final_id, accepted, reason = [], None, None, False, 'containment_rejected'
        try:
            components = validate_resource(resource)
            parent, expected_path = cap.handle, cap.path
            for index, component in enumerate(components):
                final = index == len(components) - 1
                context = dict(cap=cap, parent=parent, final=None, component_index=index, resource=resource, identity=None)
                if hook:
                    hook('after_ancestor_pin', context)
                    hook('before_component_open', context)
                state['component_index'] = index
                state['opens'] += 1
                handle = self._nt_open(component, parent, directory=not final)
                owned.append(handle)
                if final:
                    state['target_handle'] = handle
                    state['protection_live'] = True
                    state['trace'].append(dict(event='target_handle_acquired', target_handle_token=1,
                                               protection_live=True, **handle.reader_profile))
                state['peak'] = max(state['peak'], len(cap.handles) + len(owned))
                if state['slow']:
                    raise Reject('observation_threshold')
                expected_path += '\\' + component
                if final and hook:
                    context['final'] = handle
                    hook('after_final_open_before_metadata', context)
                meta = self.metadata(handle, directory=not final)
                if state['slow']:
                    raise Reject('observation_threshold')
                if final:
                    state['fault_hit'] = fault in ('volume', 'file_id', 'nondisk', 'malformed_metadata', 'metadata_query_failure', 'delete_pending')
                    if fault == 'metadata_query_failure':
                        # Real full metadata/type/path checks precede this
                        # supplemental modeled query-return failure.
                        state['fault_query_handle'] = handle.value
                        self._info(handle, 18, FILE_ID_INFO)
                    meta = self._fault_metadata(meta, fault)
                self._validate_meta(meta, expected_path, cap.identity[0], directory=not final)
                if not final:
                    parent = handle
                    continue
                final_id = meta.identity
                if final_id in cap.forbidden_ids or final_id in self.forbidden_ids:
                    raise Reject('outside_identity')
                if expected_identity is not None and final_id != expected_identity:
                    raise Reject('unexpected_identity')
                if meta.nlink != 1:
                    raise Reject('hard_link_rejected')
                if meta.size > MAX_BYTES:
                    raise Reject('size_limit_exceeded')
                state['target_verified'] = True
                state['target_identity'] = final_id
                context['identity'] = final_id
                if hook:
                    hook('before_first_content_read', context)
                chunks = []
                for offset in range(0, meta.size, 4096):
                    wanted = min(4096, meta.size - offset)
                    chunk = self._read_data(handle, offset, wanted, final_id, cap, expected_identity)
                    if len(chunk) != wanted:
                        raise Reject('short_read')
                    chunks.append(chunk)
                if self._read_data(handle, meta.size, 1, final_id, cap, expected_identity):
                    raise Reject('resource_changed')
                self._require_target_live(handle)
                after = self.metadata(handle)
                self._validate_meta(after, expected_path, cap.identity[0], directory=False)
                if (after.identity != meta.identity or after.nlink != 1 or after.size != meta.size
                        or after.write_time != meta.write_time or after.change_time != meta.change_time):
                    raise Reject('resource_changed')
                self._require_target_live(handle)
                state['trace'].append(dict(event='post_read_verified', target_handle_token=1,
                                           protection_live=True, identity=final_id))
                output, accepted, reason = b''.join(chunks), True, 'completed'
        except Reject as error:
            reason = str(error)
        except NativeError as error:
            reason = 'native_status_' + format(error.status, '08x') + '_winerror_' + str(error.winerror)
        finally:
            close_failed = False
            for handle in reversed(owned):
                try:
                    handle.close()
                    if handle is state['target_handle']:
                        state['protection_live'] = False
                        state['trace'].append(dict(event='target_handle_closed', target_handle_token=1,
                                                   protection_live=False))
                except (Reject, NativeError):
                    close_failed = True
            self._attempt = None
            elapsed = time.monotonic() - start
            if close_failed or self.handle_count != before:
                output, accepted, reason = None, False, 'handle_cleanup_failed'
            elif elapsed > OBSERVATION_SECONDS:
                output, accepted, reason = None, False, 'observation_threshold'
        return ProbeResult(accepted, reason, output if accepted else None, final_id, state['opens'],
                           state['metadata_queries'], state['data_requests'], state['physical_bytes'],
                           state['native_calls'], state['peak'], elapsed, before, self.handle_count,
                           tuple(state['trace']), state['unauthorized_reads'], state['fault_hit'],
                           tuple(state['queries_by_handle'].values()), state['native_maxcall_seconds'])
    @staticmethod
    def _fault_metadata(meta, fault):
        if fault == 'volume':
            return replace(meta, identity=(meta.identity[0] ^ 1, meta.identity[1]))
        if fault == 'file_id':
            identity = bytes([meta.identity[1][0] ^ 1]) + meta.identity[1][1:]
            return replace(meta, identity=(meta.identity[0], identity))
        if fault == 'nondisk':
            return replace(meta, file_type=3)
        if fault == 'malformed_metadata':
            return replace(meta, size=-1)
        if fault == 'delete_pending':
            return replace(meta, delete_pending=True)
        return meta
    def _validate_meta(self, meta, expected_path, volume, directory):
        if (not isinstance(meta.identity[0], int) or len(meta.identity[1]) != 16
                or meta.size < 0 or meta.nlink < 0 or not isinstance(meta.path, str)):
            raise Reject('malformed_metadata')
        if meta.attributes & FILE_ATTRIBUTE_REPARSE_POINT or meta.tag != 0:
            state = self._active_attempt()
            if state is not None:
                state['trace'].append(dict(event='reparse_security_check', source='opened_handle_metadata',
                                           component_index=state['component_index'], directory=directory,
                                           actual_directory=meta.directory, reparse_tag=meta.tag,
                                           reparse_attribute=bool(meta.attributes & FILE_ATTRIBUTE_REPARSE_POINT),
                                           rejected=True))
            raise Reject('containment_rejected')
        if (meta.identity[0] != volume or meta.path != expected_path or meta.file_type != 1
                or meta.directory != directory or meta.delete_pending
                or meta.attributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DEVICE) or meta.tag != 0):
            raise Reject('containment_rejected')
    def _require_target_live(self, handle):
        state = self._active_attempt()
        if (state is None or state['target_handle'] is not handle or not state['protection_live']
                or not state['target_verified'] or not handle.value or handle not in self._handles):
            raise Reject('target_protection_lost')
        profile = handle.reader_profile
        if (profile is None or profile['desired_access'] != 0x00100081 or profile['share_mode'] != 1
                or profile['create_options'] != 0x00200060 or profile['object_attributes'] != 0x1000
                or not profile['parent_relative']):
            raise Reject('target_protection_profile_mismatch')
        return state
    def _read_data(self, handle, offset, count, identity, cap, expected_identity):
        state = self._require_target_live(handle)
        # Oracle checks precede every actual data call, including EOF probe.
        if (identity != state['target_identity'] or identity in cap.forbidden_ids or identity in self.forbidden_ids
                or (expected_identity is not None and identity != expected_identity)):
            state['unauthorized_reads'] += 1
            raise Reject('outside_identity')
        state['data_requests'] += 1
        if state['data_requests'] > MAX_DATA_REQUESTS or state['physical_bytes'] + count > MAX_PHYSICAL_BYTES:
            raise Reject('read_bound')
        state['trace'].append(dict(event='data_request', identity=identity, offset=offset, requested=count,
                                   target_handle_token=state['target_handle_token'], protection_live=True))
        buffer, ios, position = C.create_string_buffer(count), IO_STATUS_BLOCK(), C.c_int64(offset)
        status = self._invoke('NtReadFile', self.ntdll.NtReadFile, HANDLE(handle.value), None, None, None,
                              C.byref(ios), buffer, count, C.byref(position), None)
        if status == 0x103:
            self._drain_pending(handle, (buffer, ios, position))
            raise Reject('unsupported_native_completion')
        if status & 0xffffffff == 0xc0000011:
            actual = 0
        elif status < 0:
            code = self._invoke('RtlNtStatusToDosError', self.ntdll.RtlNtStatusToDosError, status)
            raise NativeError('NtReadFile', status, code)
        elif status == 0:
            actual = ios.Information
        else:
            raise Reject('unsupported_native_completion')
        if actual > count:
            raise Reject('malformed_read')
        state['physical_bytes'] += actual
        return bytes(buffer.raw[:actual])
    def _set_information(self, handle, kind, payload):
        buffer, ios = C.create_string_buffer(payload), IO_STATUS_BLOCK()
        status = self._invoke('NtSetInformationFile', self.ntdll.NtSetInformationFile, HANDLE(handle.value),
                              C.byref(ios), buffer, len(payload), kind, nt=True)
        if status != 0:
            if status == 0x103:
                self._drain_pending(handle, (buffer, ios))
            raise Reject('unsupported_native_completion')
    def native_link(self, source_handle, target, replace=False, posix=False):
        self._name_operation(source_handle, target, replace, posix, True)
    def native_rename(self, source_handle, target, replace=False, posix=False):
        self._name_operation(source_handle, target, replace, posix, False)
    def _name_operation(self, handle, target, replace, posix, link):
        name = ('\\??\\' + str(Path(target))).encode('utf-16-le')
        # x64 FILE_{LINK,RENAME}_INFORMATION[_EX], filename offset20.
        flags = (1 if replace else 0) | (2 if posix else 0)
        payload = struct.pack('<I4xQI', flags, 0, len(name)) + name
        self._set_information(handle, (72 if link else 65) if posix else (11 if link else 10), payload)
    def native_unlink(self, handle, posix=False):
        self._set_information(handle, 64 if posix else 13, struct.pack('<I', 3) if posix else b'\1')
    def set_end_of_file(self, handle, size):
        self._invoke('SetFilePointerEx', self.kernel.SetFilePointerEx, HANDLE(handle.value), size, None, 0, boolean=True)
        self._invoke('SetEndOfFile', self.kernel.SetEndOfFile, HANDLE(handle.value), boolean=True)
    def write_at(self, handle, data, offset=0):
        self._invoke('SetFilePointerEx', self.kernel.SetFilePointerEx, HANDLE(handle.value), offset, None, 0, boolean=True)
        count, buffer = ULONG(), C.create_string_buffer(data)
        self._invoke('WriteFile', self.kernel.WriteFile, HANDLE(handle.value), buffer, len(data), C.byref(count), None, boolean=True)
        if count.value != len(data):
            raise Reject('fixture_short_write')
    def set_case_sensitive(self, directory):
        with self.control_open(directory, FILE_WRITE_ATTRIBUTES | FILE_READ_ATTRIBUTES, directory=True) as handle:
            flags = ULONG(1)
            self._invoke('SetFileInformationByHandle', self.kernel.SetFileInformationByHandle,
                         HANDLE(handle.value), 23, C.byref(flags), C.sizeof(flags), boolean=True)
            if not self.metadata(handle, directory=True).case_sensitive:
                raise Reject('fixture_case_sensitive_not_set')
            self.prerequisites['case_sensitive_directory_queryback'] = True
    def set_short_name(self, path, name='PLAINL~1.BIN'):
        with self.control_open(path, DELETE) as handle:
            self._invoke('SetFileShortNameW', self.kernel.SetFileShortNameW, HANDLE(handle.value), name, boolean=True)
        result = C.create_unicode_buffer(8192)
        length = self._invoke('GetShortPathNameW', self.kernel.GetShortPathNameW, str(path), result, len(result))
        if not length or length >= len(result) or result.value.rsplit('\\', 1)[-1] != name:
            raise Reject('fixture_short_name_not_set')
        self.prerequisites['explicit_short_alias_queryback'] = True
    def set_reparse(self, path, payload, expected_tag):
        with self.control_open(path, FILE_WRITE_DATA, directory=True) as handle:
            buffer, transferred = C.create_string_buffer(payload), ULONG()
            self._invoke('DeviceIoControl', self.kernel.DeviceIoControl, HANDLE(handle.value), 0x900a4,
                         buffer, len(payload), None, 0, C.byref(transferred), None, boolean=True)
            query = C.create_string_buffer(16384)
            self._invoke('DeviceIoControl', self.kernel.DeviceIoControl, HANDLE(handle.value), 0x900a8,
                         None, 0, query, len(query), C.byref(transferred), None, boolean=True)
            actual = query.raw[:transferred.value]
            if actual != payload or struct.unpack_from('<I', actual)[0] != expected_tag:
                raise Reject('fixture_reparse_queryback_mismatch')

class OwnedView:
    """One actual FILE_MAP_WRITE view; addresses remain private machinery."""
    def __init__(self, native, address, size):
        self.native, self.address, self.size = native, address, size
        native._views.add(self)
        native.views_created += 1
    @property
    def live(self):
        return bool(self.address) and self in self.native._views
    def calibrate(self):
        if not self.live or self.size != 4096:
            raise Reject('mapping_view_not_live')
        # Explicit synthetic fixture calibration, not candidate content IO.
        # No native address or byte value is included in evidence output.
        if C.string_at(self.address, self.size) != b'A' * 4096:
            raise Reject('mapping_fixture_bytes_changed')
        first = C.c_ubyte.from_address(self.address)
        try:
            first.value = 0x42
            if first.value != 0x42:
                raise Reject('mapping_view_not_writable')
        finally:
            first.value = 0x41
        if first.value != 0x41:
            raise Reject('mapping_fixture_restore_failed')
        return True
    def close(self):
        if self.address:
            self.native._invoke('UnmapViewOfFile', self.native.kernel.UnmapViewOfFile,
                                C.c_void_p(self.address), boolean=True, fixture_control=True)
            # Failed unmaps remain live in the ownership ledger.
            self.address = None
            self.native._views.discard(self)
            self.native.views_unmapped += 1

class WritableState:
    """The exact revised I14 view-first or section-first native lifecycle."""
    def __init__(self, native, path, expected_identity, kind):
        if kind not in ('view', 'section'):
            raise Reject('mapping_fixture_kind_unsupported')
        self.native, self.path, self.expected_identity, self.kind = native, path, expected_identity, kind
        self.source = self.section = self.view = None
        self.calibrated = False
    @property
    def origin_closed(self):
        return (self.source is not None and self.source.value is None
                and self.source not in self.native._handles)
    @property
    def section_closed(self):
        return (self.section is not None and self.section.value is None
                and self.section not in self.native._handles)
    @property
    def view_live(self):
        return self.view is not None and self.view.live
    @property
    def section_live(self):
        return (self.section is not None and bool(self.section.value)
                and self.section in self.native._handles)
    def snapshot(self):
        return dict(origin_closed=self.origin_closed, section_closed=self.section_closed,
                    view_live=self.view_live, section_live=self.section_live,
                    calibrated=self.calibrated)
    def __enter__(self):
        if self.native._active_attempt() is not None:
            raise Reject('mapping_fixture_setup_inside_reader')
        try:
            self.source = self.native.fixture_writer_open(self.path)
            meta = self.native.metadata(self.source)
            self.native._validate_meta(meta, '\\\\?\\' + str(self.path),
                                       self.expected_identity[0], directory=False)
            if meta.identity != self.expected_identity or meta.size != 4096 or meta.nlink != 1:
                raise Reject('mapping_fixture_identity_or_shape')
            self.section = self.native._fixture_section(self.source)
            self.view = self.native._fixture_view(self.section)
            self.calibrated = self.view.calibrate()
            if self.kind == 'view':
                # The view keeps the section alive internally; no writer or
                # section HANDLE remains to explain the reader conflict.
                self.source.close()
                self.section.close()
            else:
                # Prove writable section capability first, then remove its
                # calibration view before acquiring the reader.
                self.view.close()
                self.source.close()
            if not self.prove_live():
                raise Reject('mapping_fixture_lifecycle_unverified')
            return self
        except BaseException:
            self.close()
            raise
    def prove_live(self):
        if not self.origin_closed or not self.calibrated:
            return False
        if self.kind == 'view':
            if not self.section_closed or not self.view_live or self.section_live:
                return False
            self.calibrated = self.view.calibrate()
            return self.calibrated
        return self.section_live and not self.view_live and self.native.view_count == 0
    def close(self):
        errors = []
        # Attempt every independent release. A failed release stays enrolled
        # for honest handle/view baseline and cleanup failure accounting.
        for owned in (self.view, self.section, self.source):
            if owned is not None:
                try:
                    owned.close()
                except BaseException as error:
                    errors.append(type(error).__name__)
        if errors:
            raise Reject('mapping_fixture_cleanup_failed')
        if self.view_live or self.section_live or (self.source is not None and self.source.value):
            raise Reject('mapping_fixture_cleanup_unverified')
        return True
    def __exit__(self, *_):
        self.close()

class RootCapability:
    def __init__(self, native, path):
        self.native, self.handles, self.closed, self.forbidden_ids = native, [], False, set()
        if not path.is_absolute() or path.drive != 'C:' or str(path).startswith('\\\\'):
            raise Reject('unsupported_root')
        if len(str(path).encode('utf-16-le')) // 2 + MAX_RESOURCE_UNITS + 4 >= 8192:
            raise Reject('root_name_bound')
        try:
            if native._invoke('GetDriveTypeW', native.kernel.GetDriveTypeW, 'C:\\') != 3:
                raise Reject('unsupported_root_volume')
            current = native._nt_open('\\??\\C:\\', directory=True)
            self.handles.append(current)
            current_path = '\\\\?\\C:\\'
            meta = native.metadata(current, directory=True)
            root_volume = meta.identity[0]
            native._validate_meta(meta, current_path, root_volume, True)
            if len(path.parts) > 32:
                raise Reject('root_handle_bound')
            for part in path.parts[1:]:
                current = native._nt_open(part, current, directory=True)
                self.handles.append(current)
                current_path = current_path.rstrip('\\') + '\\' + part
                meta = native.metadata(current, directory=True)
                native._validate_meta(meta, current_path, root_volume, True)
                if meta.case_sensitive:
                    raise Reject('case_sensitive_root')
            self.handle, self.path, self.identity = current, current_path, meta.identity
            filesystem, serial, max_component, flags = C.create_unicode_buffer(32), ULONG(), ULONG(), ULONG()
            native._invoke('GetVolumeInformationByHandleW', native.kernel.GetVolumeInformationByHandleW,
                           HANDLE(current.value), None, 0, C.byref(serial), C.byref(max_component), C.byref(flags), filesystem, len(filesystem), boolean=True)
            if filesystem.value != 'NTFS':
                raise Reject('unsupported_root_filesystem')
            self.volume_features = flags.value
        except BaseException:
            self.close()
            raise
    def read(self, resource, expected_identity=None, hook=None, fault=None):
        return self.native.read(self, resource, expected_identity, hook, fault)
    def close(self):
        if not self.closed:
            errors = []
            for handle in reversed(self.handles):
                try:
                    handle.close()
                except (NativeError, Reject):
                    errors.append('root_pin_close_failed')
            self.closed = not any(handle.value for handle in self.handles)
            if errors:
                raise Reject('root_pin_cleanup_failed')
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()

class GUID(C.Structure):
    _fields_ = [('Data1', ULONG), ('Data2', USHORT), ('Data3', USHORT), ('Data4', C.c_ubyte * 8)]
    @classmethod
    def from_uuid(cls, value):
        return cls.from_buffer_copy(value.bytes_le)
class VIRTUAL_STORAGE_TYPE(C.Structure):
    _fields_ = [('DeviceId', ULONG), ('VendorId', GUID)]
class CREATE_VIRTUAL_DISK_V1(C.Structure):
    _fields_ = [('UniqueId', GUID), ('MaximumSize', C.c_uint64), ('BlockSizeInBytes', ULONG),
                ('SectorSizeInBytes', ULONG), ('ParentPath', C.c_wchar_p), ('SourcePath', C.c_wchar_p)]
class CREATE_VIRTUAL_DISK_PARAMETERS(C.Structure):
    _fields_ = [('Version', ULONG), ('Version1', CREATE_VIRTUAL_DISK_V1)]
class ATTACH_PARAMETERS(C.Structure):
    _fields_ = [('Version', ULONG), ('Reserved', ULONG)]

class OwnedWorkspace:
    """Known-path ownership ledger; cleanup never enumerates/follows trees."""
    def __init__(self, native):
        self.native = native
        self.root = TEMP_PARENT / ('aio-058-containment-' + uuid.uuid4().hex)
        self.repo, self.outside, self.evidence = (self.root / part for part in ('repo', 'outside', 'evidence'))
        self._entries, self._volumes, self._children, self.cleanup_errors = [], [], [], []
        self.closed = False
        self._parent_cap = None
        self.roots_created, self.roots_cleaned = native.roots_created, native.roots_cleaned
        self.cleanup_failures = self.cleanup_errors
    def __enter__(self):
        if (self.root.parent != TEMP_PARENT or not re.fullmatch(r'aio-058-containment-[0-9a-f]{32}', self.root.name)
                or os.path.lexists(self.root)):
            raise Reject('invalid_workspace_root')
        self._parent_cap = self.native.pin_root(TEMP_PARENT)
        self.native.prerequisites.update(filesystem='NTFS', drive_type=3,
                                         volume_id=self._parent_cap.identity[0],
                                         volume_features=self._parent_cap.volume_features)
        try:
            self.root.mkdir()
            self.native.roots_created.append(str(self.root))
            self._entries.append((self.root, True))
            print('OWNED_ROOT_CREATED ' + json.dumps(str(self.root)), flush=True)
            for name in ('repo', 'outside', 'evidence'):
                self.mkdir(name)
            self.file('outside/sentinel.bin', OUTSIDE_BYTES)
            return self
        except BaseException:
            self.cleanup()
            raise
    def path(self, relative):
        candidate = Path(relative)
        if '..' in candidate.parts:
            raise Reject('fixture_path_escape')
        if candidate.is_absolute():
            candidate = Path(os.path.abspath(candidate))
        else:
            candidate = self.root / candidate
        root_text, candidate_text = str(self.root), str(candidate)
        if candidate_text != root_text and not candidate_text.startswith(root_text + '\\'):
            raise Reject('fixture_path_escape')
        return candidate
    def note(self, path, directory=False):
        path = self.path(path)
        # WindowsPath equality folds case; ownership records must preserve
        # both actual a.bin and A.bin in the required case-sensitive fixture.
        if not any(str(item) == str(path) for item, _ in self._entries):
            self._entries.append((path, directory))
        return path
    def forget(self, path):
        path = self.path(path)
        self._entries = [(item, kind) for item, kind in self._entries if str(item) != str(path)]
    def mkdir(self, relative):
        path = self.path(relative)
        if path == self.root:
            return path
        if path.parent != self.root and not any(str(item) == str(path.parent) for item, _ in self._entries):
            self.mkdir(path.parent)
        if not os.path.lexists(path):
            path.mkdir()
            self.note(path, True)
        return path
    def file(self, relative, data):
        path = self.path(relative)
        self.mkdir(path.parent)
        with path.open('xb') as stream:
            self.note(path)
            if stream.write(data) != len(data):
                raise Reject('fixture_short_write')
        return path
    def symlink(self, relative, target, directory=False):
        path, target = self.path(relative), self.path(target)
        self.mkdir(path.parent)
        os.symlink(target, path, target_is_directory=directory)
        self.note(path, directory)
        return path
    def hardlink(self, relative, target):
        path, target = self.path(relative), self.path(target)
        self.mkdir(path.parent)
        os.link(target, path)
        self.note(path)
        return path
    def junction(self, relative, target):
        path, target = self.mkdir(relative), self.path(target)
        substitute, printed = ('\\??\\' + str(target)).encode('utf-16-le'), str(target).encode('utf-16-le')
        data = struct.pack('<HHHH', 0, len(substitute), len(substitute) + 2, len(printed)) + substitute + b'\0\0' + printed + b'\0\0'
        self.native.set_reparse(path, struct.pack('<IHH', MOUNT_POINT_TAG, len(data), 0) + data, MOUNT_POINT_TAG)
        return path
    def custom_reparse(self, relative):
        # The locked opaque slot is the final FILE_NON_DIRECTORY_FILE
        # component. A directory would fail its type-specific open before
        # either reparse security guard could be observed.
        path = self.file(relative, b'')
        self.native.set_reparse(path, struct.pack('<IHH', CUSTOM_TAG, 4, 0) + CUSTOM_GUID.bytes_le + b'AIOX', CUSTOM_TAG)
        return path
    def unlink(self, relative):
        path = self.path(relative)
        if os.path.lexists(path):
            directory = next((kind for item, kind in self._entries if str(item) == str(path)), False)
            os.rmdir(path) if directory else os.unlink(path)
    def relocate_known(self, source, destination):
        source, destination = self.path(source), self.path(destination)
        source_text, destination_text = str(source), str(destination)
        updated = []
        for path, directory in self._entries:
            text = str(path)
            if text == source_text or text.startswith(source_text + '\\'):
                path = Path(destination_text + text[len(source_text):])
            updated.append((path, directory))
        self._entries = updated
    def mounted_volume(self, relative):
        """Actual second NTFS volume, with exactly one fixed host-control child.

        Focus derives ONLY from GetVirtualDiskPhysicalPath on the owned live
        attachment. No discovery/guessed IDs/drive letter/privilege changes.
        """
        mount, vhd = self.mkdir(relative), self.path('evidence/second-owned-volume.vhd')
        self.note(vhd)
        dll = C.WinDLL(SYSTEM32 + r'\virtdisk.dll', use_last_error=True)
        dll.CreateVirtualDisk.argtypes = [C.POINTER(VIRTUAL_STORAGE_TYPE), C.c_wchar_p, ULONG, C.c_void_p, ULONG, ULONG, C.POINTER(CREATE_VIRTUAL_DISK_PARAMETERS), C.c_void_p, C.POINTER(HANDLE)]
        dll.CreateVirtualDisk.restype = ULONG
        dll.AttachVirtualDisk.argtypes, dll.AttachVirtualDisk.restype = [HANDLE, C.c_void_p, ULONG, ULONG, C.POINTER(ATTACH_PARAMETERS), C.c_void_p], ULONG
        dll.GetVirtualDiskPhysicalPath.argtypes, dll.GetVirtualDiskPhysicalPath.restype = [HANDLE, C.POINTER(ULONG), C.c_wchar_p], ULONG
        dll.DetachVirtualDisk.argtypes, dll.DetachVirtualDisk.restype = [HANDLE, ULONG, ULONG], ULONG
        if (C.sizeof(GUID) != 16 or C.sizeof(VIRTUAL_STORAGE_TYPE) != 20
                or C.sizeof(CREATE_VIRTUAL_DISK_PARAMETERS) != 56 or C.sizeof(ATTACH_PARAMETERS) != 8):
            raise Reject('unsupported_virtual_disk_abi')
        storage = VIRTUAL_STORAGE_TYPE(2, GUID.from_uuid(uuid.UUID('ec984aec-a0f9-47e9-901f-71415a66345b')))
        parameters = CREATE_VIRTUAL_DISK_PARAMETERS(1, CREATE_VIRTUAL_DISK_V1(GUID.from_uuid(uuid.uuid4()), 64 * 1024 * 1024, 0, 512, None, None))
        output = HANDLE()
        error = dll.CreateVirtualDisk(C.byref(storage), str(vhd), 0x003f0000, None, 0, 0, C.byref(parameters), None, C.byref(output))
        if error:
            raise NativeError('CreateVirtualDisk', 0, error)
        disk_handle = Handle(self.native, output.value)
        record = dict(dll=dll, handle=disk_handle, mount=mount, attached=False, mounted=False, file_pin=None)
        self._volumes.append(record)
        attachment = ATTACH_PARAMETERS(1, 0)
        error = dll.AttachVirtualDisk(HANDLE(disk_handle.value), None, 2, 0, C.byref(attachment), None)
        if error:
            raise NativeError('AttachVirtualDisk', 0, error)
        record['attached'] = True
        record['file_pin'] = self.native.control_open(vhd, FILE_READ_ATTRIBUTES, share=3)
        image_meta = self.native.metadata(record['file_pin'])
        if image_meta.path != '\\\\?\\' + str(vhd) or image_meta.tag or image_meta.directory:
            raise Reject('owned_vhd_identity_unverified')
        def physical_path():
            buffer, size = C.create_unicode_buffer(128), ULONG(256)
            error = dll.GetVirtualDiskPhysicalPath(HANDLE(disk_handle.value), C.byref(size), buffer)
            if error:
                raise NativeError('GetVirtualDiskPhysicalPath', 0, error)
            if not re.fullmatch(r'\\\\\.\\PhysicalDrive[0-9]{1,6}', buffer.value):
                raise Reject('owned_virtual_disk_mapping_unverified')
            return buffer.value
        physical = physical_path()
        number = int(physical.rsplit('PhysicalDrive', 1)[1])
        script = self.file('evidence/owned-volume-diskpart.txt',
                           (f'select vdisk file="{vhd}"\r\nselect disk {number}\r\nconvert mbr\r\ncreate partition primary\r\n'
                            f'format fs=ntfs quick label=AIO058\r\nassign mount="{mount}"\r\nexit\r\n').encode('ascii'))
        if physical_path() != physical or self.native.metadata(record['file_pin']).identity != image_meta.identity:
            raise Reject('owned_virtual_disk_mapping_changed')
        log = self.path('evidence/owned-volume-diskpart-output.txt')
        self.note(log)
        child_input = self.file('evidence/owned-volume-diskpart-input.txt', b'')
        with log.open('xb') as stream, child_input.open('rb') as input_stream:
            child = subprocess.Popen([SYSTEM32 + r'\diskpart.exe', '/s', str(script)], stdin=input_stream,
                                     stdout=stream, stderr=subprocess.STDOUT, shell=False, close_fds=True,
                                     cwd=str(self.evidence), creationflags=0x08000000)
            self._children.append(child)
            self.native.children_created += 1
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                try:
                    child.kill()
                finally:
                    # Even a failed termination attempt cannot abandon this
                    # exact child. Wait for actual exit before releasing scope.
                    child.wait()
                raise Reject('owned_fixture_child_timeout') from None
            finally:
                if child.poll() is not None:
                    self.native.children_reaped += 1
                    self._children.remove(child)
        if child.returncode != 0:
            raise Reject('owned_volume_fixture_child_failed')
        if log.stat().st_size > 65536:
            raise Reject('owned_fixture_output_bound')
        filesystem, serial, max_component, flags = C.create_unicode_buffer(32), ULONG(), ULONG(), ULONG()
        self.native._invoke('GetVolumeInformationW', self.native.kernel.GetVolumeInformationW,
                            str(mount) + '\\', None, 0, C.byref(serial), C.byref(max_component), C.byref(flags), filesystem, len(filesystem), boolean=True)
        if filesystem.value != 'NTFS':
            raise Reject('owned_second_volume_not_ntfs')
        record['mounted'] = True
        with self.native.control_open(mount, directory=True, nofollow=False) as mounted_handle:
            mounted_meta = self.native.metadata(mounted_handle, directory=True)
            if mounted_meta.identity[0] == self._parent_cap.identity[0]:
                raise Reject('owned_second_volume_not_distinct')
            if self.native.kernel.GetDriveTypeW(str(mount) + '\\') != 3:
                raise Reject('owned_second_volume_not_local_fixed')
            self.native.prerequisites['second_ntfs_volume_id'] = mounted_meta.identity[0]
        # This synthetic target is on the verified owned virtual volume,
        # never an operational/protected volume. Detach then deleting the
        # owned image destroys all of its contents without directory scans.
        volume_sentinel = self.file(mount / 'sentinel.bin', OUTSIDE_BYTES)
        self.native.forbidden_ids.add(self.native.identity(volume_sentinel))
        with self.native.control_open(mount, directory=True) as handle:
            if self.native.metadata(handle, directory=True).tag != MOUNT_POINT_TAG:
                raise Reject('owned_volume_mount_tag_missing')
        return mount
    def cleanup(self):
        try:
            self._cleanup_known()
        finally:
            if self._parent_cap:
                try:
                    self._parent_cap.close()
                except (NativeError, Reject):
                    self.cleanup_errors.append('parent_pin_close_failed')
                    raise Reject('workspace_cleanup_failed') from None
    def _cleanup_known(self):
        if self.closed:
            return
        self.closed = True
        for child in tuple(self._children):
            try:
                try:
                    if child.poll() is None:
                        child.kill()
                finally:
                    child.wait()
            except BaseException:
                self.cleanup_errors.append('owned_child_reap_failed')
            finally:
                if child.poll() is not None:
                    self.native.children_reaped += 1
                    self._children.remove(child)
        if self._children:
            raise Reject('live_owned_child_at_cleanup')
        for record in reversed(self._volumes):
            # Attempt all independent releases even if an earlier one failed.
            try:
                ok = self.native.kernel.DeleteVolumeMountPointW(str(record['mount']) + '\\')
                if not ok and record['mounted']:
                    raise NativeError('DeleteVolumeMountPointW', 0, C.get_last_error())
            except BaseException:
                self.cleanup_errors.append('owned_mount_cleanup_failed')
            try:
                if record['attached']:
                    error = record['dll'].DetachVirtualDisk(HANDLE(record['handle'].value), 0, 0)
                    if error:
                        raise NativeError('DetachVirtualDisk', 0, error)
            except BaseException:
                self.cleanup_errors.append('owned_volume_detach_failed')
            for handle in (record['file_pin'], record['handle']):
                try:
                    if handle:
                        handle.close()
                except BaseException:
                    self.cleanup_errors.append('owned_volume_handle_close_failed')
        if self.cleanup_errors:
            raise Reject('workspace_cleanup_failed')
        for path, directory in reversed(self._entries):
            try:
                checked = self.path(path)
                if os.path.lexists(checked):
                    os.rmdir(checked) if directory else os.unlink(checked)
            except BaseException:
                self.cleanup_errors.append('known_path_cleanup_failed')
        if not os.path.lexists(self.root) and not self.cleanup_errors:
            self.native.roots_cleaned.append(str(self.root))
        else:
            raise Reject('workspace_cleanup_failed')
    def __exit__(self, *_):
        self.cleanup()

def main():
    print(json.dumps(dict(noncanonical=True, matrix_executed=False, launcher='tests.test_aio_058_windows_containment_experiment')))
    return 2
if __name__ == '__main__':
    raise SystemExit(main())
