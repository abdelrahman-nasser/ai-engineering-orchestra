"""Private native Windows/NTFS repository_file_read implementation, v1.

Handle-relative traversal is mandatory; there is no pathname reader fallback.
Share READ only protects the current opened read window, not an atomic content
snapshot or historical link provenance. nlink==1 is a current restriction.
Native synchronous calls have bounded work, not a hard wall-time guarantee.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes as C
from dataclasses import dataclass
import os
from pathlib import Path
import re
from threading import Condition, Lock, get_ident, local

from itru.agent_execution_authorization_grant_producer import _ProcessLocalCapability, _mint_capability

__all__ = ()
MAX_BYTES, MAX_PHYSICAL_BYTES, MAX_DATA_REQUESTS = 65536, 65537, 17
MAX_COMPONENTS, MAX_RESOURCE_UNITS = 16, 4096
_IMPLEMENTATION_ID = 'tool::itru-native-repository-file-read::v1'
_PENDING_BUFFERS = []
_ROOTS = []  # Genuine provisioning membership; copied IDs are never root authority.
_ROOT_BINDINGS = []  # Environment roots cannot hot swap within a Session.
_ROOT_COMPOSITION = Lock()
ULONG, USHORT, HANDLE, NTSTATUS = C.c_uint32, C.c_uint16, C.c_void_p, C.c_int32


class _NativeFailure(Exception):
    def __init__(self, reason, winerror=0):
        super().__init__(reason)
        self.reason, self.winerror = reason, winerror


class _UnverifiedCompletion(BaseException):
    """Fatal support violation; native buffer lifetime cannot be certified."""


def _resource_components(resource):
    if type(resource) is not str or not resource or resource.startswith('/'):
        raise _NativeFailure('containment_rejected')
    try:
        units = len(resource.encode('utf-16-le', errors='strict')) // 2
    except UnicodeError:
        raise _NativeFailure('containment_rejected') from None
    pieces = tuple(resource.split('/'))
    if units > MAX_RESOURCE_UNITS or len(pieces) > MAX_COMPONENTS:
        raise _NativeFailure('containment_rejected')
    for piece in pieces:
        if (not piece or piece in ('.', '..') or piece.endswith(('.', ' '))
                or any(ord(c) < 32 or c in '\\:<>"|?*' for c in piece)):
            raise _NativeFailure('containment_rejected')
        stem = piece.split('.', 1)[0].upper()
        if stem in {'CON','PRN','AUX','NUL','CONIN$','CONOUT$'} or re.fullmatch(r'(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]', stem):
            raise _NativeFailure('containment_rejected')
    return pieces


class _Unicode(C.Structure):
    _fields_ = [('Length', USHORT), ('MaximumLength', USHORT), ('Buffer', C.c_void_p)]
class _Attributes(C.Structure):
    _fields_ = [('Length', ULONG), ('RootDirectory', HANDLE), ('ObjectName', C.POINTER(_Unicode)),
                ('Attributes', ULONG), ('SecurityDescriptor', C.c_void_p), ('SecurityQualityOfService', C.c_void_p)]
class _IOSUnion(C.Union):
    _fields_ = [('Status', NTSTATUS), ('Pointer', C.c_void_p)]
class _IOS(C.Structure):
    _anonymous_ = ('u',)
    _fields_ = [('u', _IOSUnion), ('Information', C.c_size_t)]
class _Standard(C.Structure):
    _fields_ = [('AllocationSize', C.c_int64), ('EndOfFile', C.c_int64), ('NumberOfLinks', ULONG),
                ('DeletePending', C.c_ubyte), ('Directory', C.c_ubyte)]
class _Basic(C.Structure):
    _fields_ = [('CreationTime', C.c_int64), ('LastAccessTime', C.c_int64), ('LastWriteTime', C.c_int64),
                ('ChangeTime', C.c_int64), ('FileAttributes', ULONG)]
class _ID(C.Structure):
    _fields_ = [('VolumeSerialNumber', C.c_uint64), ('FileId', C.c_ubyte * 16)]
class _Tag(C.Structure):
    _fields_ = [('FileAttributes', ULONG), ('ReparseTag', ULONG)]


@dataclass(frozen=True, slots=True)
class _Metadata:
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
    case_sensitive: bool


class _Handle:
    def __init__(self, native, value):
        self.native, self.value = native, value
        native.handles.add(self)
    def close(self):
        if any(handle.native is self.native for handle,_ in _PENDING_BUFFERS):
            raise _UnverifiedCompletion('native_completion_unverified')
        if self.value:
            self.native.call('CloseHandle', HANDLE(self.value), boolean=True)
            self.value = None
            self.native.handles.remove(self)


class _Native:
    """Fixed System32 ABI only. No discovery, subprocess or dynamic adapter."""
    def __init__(self):
        if os.name != 'nt' or C.sizeof(C.c_void_p) != 8:
            raise _NativeFailure('adapter_unavailable')
        self.kernel = C.WinDLL(r'C:\Windows\System32\kernel32.dll', use_last_error=True)
        self.ntdll = C.WinDLL(r'C:\Windows\System32\ntdll.dll', use_last_error=True)
        self.handles, self.thread = set(), local()
        self.unavailable = False
        signatures = {
            'CloseHandle': ([HANDLE], C.c_int),
            'GetFileInformationByHandleEx': ([HANDLE,C.c_int,C.c_void_p,ULONG],C.c_int),
            'GetFileType': ([HANDLE],ULONG),
            'GetFinalPathNameByHandleW': ([HANDLE,C.c_wchar_p,ULONG,ULONG],ULONG),
            'GetVolumeInformationByHandleW': ([HANDLE,C.c_wchar_p,ULONG,C.POINTER(ULONG),C.POINTER(ULONG),C.POINTER(ULONG),C.c_wchar_p,ULONG],C.c_int),
            'GetDriveTypeW': ([C.c_wchar_p],ULONG),
        }
        self.functions = {}
        for name,(args,result) in signatures.items():
            f = getattr(self.kernel,name)
            f.argtypes,f.restype = args,result
            self.functions[name] = f
        for name,args,result in (
            ('NtCreateFile',[C.POINTER(HANDLE),ULONG,C.POINTER(_Attributes),C.POINTER(_IOS),C.POINTER(C.c_int64),ULONG,ULONG,ULONG,ULONG,C.c_void_p,ULONG],NTSTATUS),
            ('NtReadFile',[HANDLE,HANDLE,C.c_void_p,C.c_void_p,C.POINTER(_IOS),C.c_void_p,ULONG,C.POINTER(C.c_int64),C.POINTER(ULONG)],NTSTATUS),
            ('NtWaitForSingleObject',[HANDLE,C.c_ubyte,C.POINTER(C.c_int64)],NTSTATUS),
            ('RtlNtStatusToDosError',[NTSTATUS],ULONG),
        ):
            f=getattr(self.ntdll,name)
            f.argtypes,f.restype=args,result
            self.functions[name]=f
        self.abi = tuple((name,function,tuple(function.argtypes),function.restype) for name,function in self.functions.items())
        if (C.sizeof(_Attributes),C.sizeof(_IOS),C.sizeof(_Standard),C.sizeof(_Basic),C.sizeof(_ID)) != (48,16,24,40,24):
            raise _NativeFailure('adapter_unavailable')

    def abi_available(self):
        try:
            return tuple((name,function,tuple(function.argtypes),function.restype)
                for name,function in self.functions.items())==self.abi
        except (TypeError,AttributeError):
            return False

    def call(self,name,*args,boolean=False):
        budget = getattr(self.thread,'budget',None)
        if budget is not None:
            budget['calls'] += 1
            if budget['calls'] > 253:
                raise _NativeFailure('read_failure')
        result = self.functions[name](*args)
        if boolean and not result:
            raise _NativeFailure('read_failure',C.get_last_error())
        return result

    def pending(self,handle,keepalive):
        self.unavailable = True
        retained = (handle,keepalive)
        _PENDING_BUFFERS.append(retained)
        if self.call('NtWaitForSingleObject',HANDLE(handle.value),False,None) != 0:
            raise _UnverifiedCompletion('native_completion_unverified')
        _PENDING_BUFFERS.remove(retained)
        raise _NativeFailure('adapter_unavailable')

    def open_component(self,component,parent=None,directory=False):
        encoded=component.encode('utf-16-le',errors='strict')
        if len(encoded)>16382:
            raise _NativeFailure('containment_rejected')
        buffer=C.create_string_buffer(encoded+b'\0\0')
        name=_Unicode(len(encoded),len(encoded)+2,C.cast(buffer,C.c_void_p))
        attributes=_Attributes(C.sizeof(_Attributes),HANDLE(parent.value) if parent else None,C.pointer(name),0x1000 if parent else 0,None,None)
        output,ios=HANDLE(),_IOS()
        options=0x00200000|0x20|(1 if directory else 0x40)
        access=0x80|0x100000|(0x20 if directory else 1)
        status=self.call('NtCreateFile',C.byref(output),access,C.byref(attributes),C.byref(ios),None,0,1,1,options,None,0)
        if status<0:
            code=self.call('RtlNtStatusToDosError',status)
            reason = 'resource_missing' if code in (2,3) else 'containment_rejected' if code in (32,4390,4391,4392,4393,1920,681) else 'read_failure'
            raise _NativeFailure(reason,code)
        if not output.value:
            raise _NativeFailure('read_failure')
        handle=_Handle(self,output.value)
        try:
            if status==0x103:
                self.pending(handle,(buffer,name,attributes,ios,output))
            if status!=0:
                self.unavailable = True
                raise _NativeFailure('adapter_unavailable')
            return handle
        except Exception:
            handle.close()
            raise

    def info(self,handle,kind,structure):
        budget=getattr(self.thread,'budget',None)
        if budget is not None:
            count=budget['queries'].get(handle.value,0)+1
            budget['queries'][handle.value]=count
            if count>12:
                raise _NativeFailure('read_failure')
        result=structure()
        self.call('GetFileInformationByHandleEx',HANDLE(handle.value),kind,C.byref(result),C.sizeof(result),boolean=True)
        return result

    def metadata(self,handle,directory=False):
        standard,basic=self.info(handle,1,_Standard),self.info(handle,0,_Basic)
        identity,tag=self.info(handle,18,_ID),self.info(handle,9,_Tag)
        file_type=self.call('GetFileType',HANDLE(handle.value))
        path=C.create_unicode_buffer(8192)
        length=self.call('GetFinalPathNameByHandleW',HANDLE(handle.value),path,len(path),0)
        if not length or length>=len(path):
            raise _NativeFailure('containment_rejected')
        sensitive=bool(self.info(handle,23,ULONG).value&1) if directory else False
        if (standard.EndOfFile<0 or standard.AllocationSize<0 or tag.FileAttributes!=basic.FileAttributes
                or bool(standard.Directory)!=bool(basic.FileAttributes&0x10)):
            raise _NativeFailure('containment_rejected')
        return _Metadata((identity.VolumeSerialNumber,bytes(identity.FileId)),path.value,standard.EndOfFile,
            standard.NumberOfLinks,bool(standard.Directory),bool(standard.DeletePending),basic.FileAttributes,
            tag.ReparseTag,file_type,basic.LastWriteTime,basic.ChangeTime,sensitive)

    @staticmethod
    def validate(meta,path,volume,directory):
        if (type(meta.identity[0]) is not int or type(meta.identity[1]) is not bytes
                or type(meta.path) is not str or meta.size<0 or meta.nlink<0
                or meta.identity[0]!=volume or len(meta.identity[1])!=16 or not any(meta.identity[1])
                or meta.path!=path or meta.file_type!=1
                or meta.directory!=directory or meta.delete_pending or meta.attributes&(0x400|0x40) or meta.tag!=0):
            raise _NativeFailure('containment_rejected')

    def read_data(self,handle,offset,count,budget):
        if not handle.value or handle not in self.handles:
            raise _NativeFailure('read_failure')
        budget['requests']+=1
        budget['requested']+=count
        if budget['requests']>17 or budget['requested']>65537:
            raise _NativeFailure('read_failure')
        buffer,ios,position=C.create_string_buffer(count),_IOS(),C.c_int64(offset)
        status=self.call('NtReadFile',HANDLE(handle.value),None,None,None,C.byref(ios),buffer,count,C.byref(position),None)
        if status==0x103:
            self.pending(handle,(buffer,ios,position))
        if status&0xffffffff==0xc0000011:
            actual=0
        elif status<0:
            raise _NativeFailure('read_failure')
        elif status==0:
            actual=ios.Information
        else:
            self.unavailable = True
            raise _NativeFailure('adapter_unavailable')
        if actual>count:
            raise _NativeFailure('read_failure')
        budget['physical']+=actual
        return bytes(buffer.raw[:actual])


class _RootState:
    def __init__(self):
        self.handles=[]
        self.quarantined=[]
        self.closed=False
        self.closing=False
        self.operations=0
        self.condition=Condition()


class _TrustedRoot(_ProcessLocalCapability):
    __slots__=('_session','_environment','_pid','_native','_state','_path','_identity')

    @property
    def _closed(self):
        return self._state.closed or self._state.closing

    def _available(self,session,environment):
        genuine = next((record for record in _ROOTS if record[0] is self), None)
        return (genuine is not None and genuine[1:] == (self._session, self._environment, self._native, self._path, self._identity, tuple(self._state.handles))
            and self._session is session and self._environment==environment and self._pid==os.getpid()
            and not self._closed and not self._native.unavailable
            and not self._state.quarantined and all(h.value for h in self._state.handles)
            and self._native.abi_available())

    @contextmanager
    def _retain(self):
        # Lifecycle reservation precedes S. No lifecycle mutex spans S/G/P/W/C.
        with self._state.condition:
            if self._closed or self._pid!=os.getpid():
                raise _NativeFailure('adapter_unavailable')
            self._state.operations+=1
        try:
            yield
        finally:
            with self._state.condition:
                self._state.operations-=1
                self._state.condition.notify_all()

    def close(self):
        if self._session._thread_operations.get(get_ident(),0)>0:
            raise RuntimeError('root teardown cannot wait underneath owned operation')
        with self._state.condition:
            self._state.closing=True
            while self._state.operations:
                self._state.condition.wait()
            errors=[]
            for handle in (*reversed(self._state.quarantined),*reversed(self._state.handles)):
                try:
                    handle.close()
                except Exception:
                    errors.append('root_cleanup_failed')
            self._state.closed=not any(h.value for h in (*self._state.quarantined,*self._state.handles))
            if errors:
                raise _NativeFailure('read_failure')


def _provision_trusted_root(*,session,environment_id,path):
    """Control-plane trusted configured root, never a Run/resource-derived root.

    Caller owns the configured root/ACL profile; this cooperative composition
    is not isolation against hostile same-user/admin/kernel code. Retains every
    ancestor and refuses any root/ancestor reparse, remote volume or alias.
    """
    from itru._local_dispatch_claim_lease import _validate_owned_dispatch_context
    path=Path(path)
    if (type(environment_id) is not str or not environment_id or not path.is_absolute()
            or not re.fullmatch('[A-Z]:',path.drive) or len(path.parts)>32
            or len(str(path).encode('utf-16-le',errors='strict'))//2+4096+4>=8192):
        raise _NativeFailure('adapter_unavailable')
    from itru.windows_local_authorization_domain_owner import _WindowsOwnedAuthorizationDomainSession
    if type(session) is not _WindowsOwnedAuthorizationDomainSession:
        raise _NativeFailure('adapter_unavailable')
    # Reservation lock never nests with operational protection or native IO.
    with _ROOT_COMPOSITION:
        if any(bound_session is session and environment==environment_id for bound_session,environment in _ROOT_BINDINGS):
            raise _NativeFailure('adapter_unavailable')
        _ROOT_BINDINGS.append((session,environment_id))
    native,state=_Native(),_RootState()
    try:
        with session.operation():
            _validate_owned_dispatch_context(session,session._store)
            if native.call('GetDriveTypeW',path.drive+'\\')!=3:
                raise _NativeFailure('adapter_unavailable')
            current=native.open_component('\\??\\'+path.drive+'\\',directory=True)
            state.handles.append(current)
            current_path='\\\\?\\'+path.drive+'\\'
            meta=native.metadata(current,True)
            volume=meta.identity[0]
            native.validate(meta,current_path,volume,True)
            for component in path.parts[1:]:
                _resource_components(component)
                current=native.open_component(component,current,True)
                state.handles.append(current)
                current_path=current_path.rstrip('\\')+'\\'+component
                meta=native.metadata(current,True)
                native.validate(meta,current_path,volume,True)
                if meta.case_sensitive:
                    raise _NativeFailure('adapter_unavailable')
            filesystem,serial,max_component,flags=C.create_unicode_buffer(32),ULONG(),ULONG(),ULONG()
            native.call('GetVolumeInformationByHandleW',HANDLE(current.value),None,0,C.byref(serial),C.byref(max_component),C.byref(flags),filesystem,len(filesystem),boolean=True)
            if filesystem.value!='NTFS':
                raise _NativeFailure('adapter_unavailable')
            from itru.windows_local_authorization_domain_owner import (
                _current_user_sid, _validate_security_profile,
            )
            _validate_security_profile(path, _current_user_sid(), directory=True)
            root = _mint_capability(_TrustedRoot,dict(_session=session,_environment=environment_id,_pid=os.getpid(),
                _native=native,_state=state,_path=current_path,_identity=meta.identity))
            _ROOTS.append((root, session, environment_id, native, current_path, meta.identity, tuple(state.handles)))
        return root  # Publish only after the original ownership postcheck.
    except BaseException:
        state.closing=True
        for handle in reversed(state.handles):
            handle.close()
        state.closed=True
        raise


def _invoke_repository_file_read(continuation,root,resource):
    """Fixed synchronous leaf; rejects bypass before resource metadata/open."""
    from itru._execution_entry_and_controlled_invocation import (
        _Continuation, _ControlledInvocationCoordinator, _InvocationOutcome,
    )
    if type(continuation) is not _Continuation or type(root) is not _TrustedRoot:
        raise TypeError('original protected continuation required')
    coordinator=getattr(continuation,'_coordinator',None)
    if type(coordinator) is not _ControlledInvocationCoordinator:
        raise TypeError('genuine original coordinator required')
    _ControlledInvocationCoordinator._begin_native(coordinator,continuation,root,resource)
    native=root._native
    owned=[]
    chunks=[]
    content_started=False
    budget=dict(calls=0,queries={},requests=0,requested=0,physical=0)
    if getattr(native.thread,'budget',None) is not None:
        raise _NativeFailure('adapter_unavailable')
    native.thread.budget=budget
    result=_InvocationOutcome('failed_before_content','containment_rejected')
    try:
        components=_resource_components(resource)
        parent,path=root._state.handles[-1],root._path
        for index,component in enumerate(components):
            final=index==len(components)-1
            handle=native.open_component(component,parent,not final)
            owned.append(handle)
            path+='\\'+component
            meta=native.metadata(handle,not final)
            native.validate(meta,path,root._identity[0],not final)
            if not final:
                parent=handle
                continue
            if meta.nlink!=1:
                raise _NativeFailure('containment_rejected')
            if meta.size>65536:
                raise _NativeFailure('size_limit_exceeded')
            for offset in range(0,meta.size,4096):
                content_started=True
                wanted=min(4096,meta.size-offset)
                chunk=native.read_data(handle,offset,wanted,budget)
                if len(chunk)!=wanted:
                    raise _NativeFailure('read_failure')
                chunks.append(chunk)
            content_started=True
            if native.read_data(handle,meta.size,1,budget):
                raise _NativeFailure('resource_changed')
            after=native.metadata(handle)
            try:
                native.validate(after,path,root._identity[0],False)
            except _NativeFailure:
                raise _NativeFailure('resource_changed') from None
            if (after.identity!=meta.identity or after.nlink!=1 or after.size!=meta.size
                    or after.write_time!=meta.write_time or after.change_time!=meta.change_time):
                raise _NativeFailure('resource_changed')
            data=b''.join(chunks)
            result=_InvocationOutcome('completed','effect_completed',data,len(data))
    except _NativeFailure as error:
        result=_InvocationOutcome('failed_after_content' if content_started else 'failed_before_content',error.reason)
    except Exception:
        result=_InvocationOutcome('failed_after_content' if content_started else 'failed_before_content','read_failure')
    finally:
        failed=False
        for handle in reversed(owned):
            try:
                handle.close()
            except Exception:
                failed=True
        native.thread.budget=None
        if failed:
            # Quarantine cannot re-enable this configured root. Teardown occurs
            # outside S/G/P after all lifecycle reservations have unwound.
            root._state.quarantined.extend(handle for handle in owned if handle.value)
            root._state.closing=True
            result=_InvocationOutcome('ambiguous','effect_ambiguous')
        chunks.clear()
    return result
