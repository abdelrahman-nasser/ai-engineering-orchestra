"""AIO-058 production validation: fixed scenario IDs, no test discovery.

Storage mechanics use the reviewed AIO-057 disposable rig. Native scenarios
use genuine canonical ownership and never a mocked symlink. Privileged hostile
fixture creation is exclusively a Human control-plane step outside this repo.
"""
from __future__ import annotations

import ast
from contextlib import closing
import copy
import ctypes
from dataclasses import fields, replace
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import pickle
import sqlite3
import stat
from threading import Barrier, Event, Thread
import unittest
from unittest import mock

from engineering_orchestration import _execution_entry_and_controlled_invocation as entry
from engineering_orchestration import _native_repository_file_read as native
from engineering_orchestration import _jit_execution_attempt_authorization as jit
from engineering_orchestration import sqlite_agent_execution_dispatch_admission_store as store_module
from tests import test_jit_execution_attempt_authorization as predecessor
from tests import test_dispatch_claim_lease_foundation as claims

ROOT = Path(r'D:\Dev\ai-engineering-orchestra')
TEMP = Path(r'C:\Users\Abdelrahman\AppData\Local\Temp')
HOSTILE_ROOT = TEMP / 'aio-058-containment-8d832fd4da624cfeacb54a6a1466a1ca'
HOSTILE_BYTES = b'AIO-058 hostile fixture synthetic nonsecret\n'
FIRST_RESOURCE = 'fixtures/aio-058-first-read.bin'
FIRST_BYTES = b'AIO-058 disposable nonsecret fixture\n'
SIZES = dict(A=10,B=10,C=6,D=6,E=10,F=10,G=16,H=12,I=18,J=8,K=8,L=8,M=6)
SCENARIO_IDS = tuple(f'{group}{n:02d}' for group,size in SIZES.items() for n in range(1,size+1))
E_TRACE = {
    'E01':('A01','B01','E01'),'E02':('B03',),'E03':('B04',),'E04':('F05',),
    'E05':('F06','F07'),'E06':('C01',),'E07':('C02','F03'),'E08':('C03',),
    'E09':('A08','C04'),'E10':('D04',),'E11':('D02','D06'),'E12':('D01','D03'),
    'E13':('K02',),'E14':('K03',),'E15':('K05',),'E16':('E07','K07'),
    'E17':('F10',),'E18':('E09',),'E19':('B02',),'E20':('B10',),'E21':('F01','F02'),
    'E22':('A10',)+tuple(f'G{n:02d}' for n in range(1,17))+('H05',),
    'E23':('E08','E10'),'E24':('K06','K08'),
}


def _connect(r):
    return claims.outbox._connect(r.store.configuration.database_path)


def _enter(r, cap):
    a = r.a
    cell = a._cap_cell(cap)
    with a.session.operation():
        a._live()
        with a.guard.read_scope():
            operation = entry._EntryOperation(a,cell,r.principal,r.decision)
            request = store_module._mint_dispatch_request('query',a.session,a.store,
                capability=cell.subject.executor,claim_id=cell.subject.claim_id,
                identity=cell.subject.dispatch_identity,generation=cell.subject.lease_generation,mode='current')
            return a.store._enter_execution(request,operation)


def _history(r, cap):
    a=r.a
    try:
        with a.session.operation():
            subject=cap._cell.subject
            request=store_module._mint_dispatch_request('query',a.session,a.store,
                capability=subject.executor,claim_id=subject.claim_id,identity=subject.dispatch_identity,
                generation=subject.lease_generation,mode='current')
            return a.store._classify_execution_entry(request)
    except (store_module.SqliteAdmissionStoreError,claims.adapter.AuthorizationDomainOwnershipError):
        return entry._EntryResult('integrity_failure')


def _count(r):
    with closing(_connect(r)) as c:
        return c.execute('SELECT COUNT(*) FROM agent_execution_entries').fetchone()[0]


def _new_generation(r, test):
    r.clock.value=max(r.clock.value,claims.T+timedelta(seconds=31))
    facade=r.fixture._other()
    claim=r.fixture._claim(33,facade)
    subject=r.a.subject(claim,facade._executor,r.run,r.binding_value)
    args=dict(provenance_reference='aio058-reclaim',valid_from=claims.T,
        valid_until=claims.T+timedelta(minutes=5))
    if r.grant.issuer_kind=='human':
        args['approval_session_id']='aio058-reclaim'
    else:
        args.update(decision='allow',policy_revision='aio058-reclaim')
    decision=r.a.mint_entry_decision(subject,r.principal,**args)
    result=r.a.prepare(subject,r.principal,decision)
    test.assertEqual(result.outcome,'prepared',result)
    r.decision=decision
    return result.capability


def _fixture_control():
    # TEST ONLY: reviewed fixture-control API, never its containment reader.
    # Production modules have no import/dependency on this nonpackaged evidence.
    from experiments.aio_058_windows_containment import windows_containment_probe as probe
    return probe


def provision_hostile_fixture():
    """Human ADMIN entrypoint: only fixed external synthetic fixture provisioning.

    Does not construct a production owner, invoke the production reader, run
    tests, alter policy, install dependencies or modify checkout files.
    """
    if not bool(ctypes.windll.shell32.IsUserAnAdmin()):
        raise AssertionError('Human Administrator fixture provisioning required')
    if os.path.lexists(HOSTILE_ROOT) or HOSTILE_ROOT.parent != TEMP:
        raise AssertionError('refusing existing or foreign fixture root')
    probe=_fixture_control()
    control=probe.Native()
    workspace=probe.OwnedWorkspace(control)
    workspace.root=HOSTILE_ROOT
    workspace.repo,workspace.outside,workspace.evidence=(HOSTILE_ROOT/name for name in ('repo','outside','evidence'))
    workspace.__enter__()
    success=False
    try:
        workspace.mkdir('owned-target')
        target=workspace.file('owned-target/synthetic.bin',HOSTILE_BYTES)
        from engineering_orchestration.windows_local_authorization_domain_owner import _apply_security_profile,_current_user_sid
        sid=_current_user_sid()
        for directory in (HOSTILE_ROOT,workspace.repo,workspace.outside,HOSTILE_ROOT/'owned-target'):
            _apply_security_profile(directory,sid,directory=True)
        workspace.symlink('repo/file-link',target)
        workspace.symlink('repo/directory-link',target.parent,True)
        workspace.junction('repo/junction',target.parent)
        workspace.custom_reparse('repo/opaque-reparse')
        case=workspace.mkdir('repo/case-sensitive')
        control.set_case_sensitive(case)
        workspace.file(case/'a.bin',b'lower')
        workspace.file(case/'A.bin',b'UPPER')
        long=workspace.file('repo/PlainLongName.bin',b'long name')
        control.set_short_name(long)
        mount=workspace.mounted_volume('repo/volume-mount')
        record=workspace._volumes[0]
        # The Administrator process exits before unelevated tests start.
        # Reattach only this owned image with permanent lifetime, no drive letter.
        code=record['dll'].DetachVirtualDisk(probe.HANDLE(record['handle'].value),0,0)
        if code:raise AssertionError('owned fixture volume detach failed')
        record['attached']=False
        attachment=probe.ATTACH_PARAMETERS(1,0)
        code=record['dll'].AttachVirtualDisk(probe.HANDLE(record['handle'].value),None,6,0,ctypes.byref(attachment),None)
        if code:raise AssertionError('owned fixture volume permanent attach failed')
        record['attached']=True
        volume_buffer=ctypes.create_unicode_buffer(128)
        function=control.kernel.GetVolumeNameForVolumeMountPointW
        function.argtypes,function.restype=[ctypes.c_wchar_p,ctypes.c_wchar_p,probe.ULONG],ctypes.c_int
        if not function(str(mount)+'\\',volume_buffer,len(volume_buffer)):
            raise AssertionError('owned fixture volume identity query failed')
        manifest=dict(contract='aio058-hostile-v1',root=str(HOSTILE_ROOT),
            sha256=hashlib.sha256(HOSTILE_BYTES).hexdigest(),volume_guid=volume_buffer.value,
            known_entries=[(str(path),directory) for path,directory in workspace._entries],
            root_identity=[control.identity(HOSTILE_ROOT)[0],control.identity(HOSTILE_ROOT)[1].hex()],
            production_invocations=0)
        marker=workspace.file('fixture-contract.json',json.dumps(manifest,sort_keys=True).encode('utf-8'))
        # Append marker's own path only to cleanup inventory, not target authority.
        manifest['known_entries'].append((str(marker),False))
        marker.write_text(json.dumps(manifest,sort_keys=True),encoding='utf-8')
        for handle in tuple(control._handles):handle.close()
        success=True
        print('FIXTURE ROOT CREATED: '+str(HOSTILE_ROOT))
        print('PRODUCTION TESTS EXECUTED: NO')
    finally:
        if not success:workspace.cleanup()


def _fixture_inventory():
    directories={'','repo','outside','evidence','owned-target','repo/directory-link',
        'repo/junction','repo/case-sensitive','repo/volume-mount'}
    files={'outside/sentinel.bin','owned-target/synthetic.bin','repo/file-link',
        'repo/opaque-reparse','repo/case-sensitive/a.bin',
        'repo/case-sensitive/A.bin','repo/PlainLongName.bin','repo/volume-mount/sentinel.bin',
        'evidence/second-owned-volume.vhd','evidence/owned-volume-diskpart.txt',
        'evidence/owned-volume-diskpart-output.txt','evidence/owned-volume-diskpart-input.txt','fixture-contract.json'}
    return {(str(HOSTILE_ROOT/name),True) for name in directories}|{(str(HOSTILE_ROOT/name),False) for name in files}


def _plain_fixture(path,directory=False):
    value=path.lstat()  # Reject every reparse tag before a content-following API.
    if (value.st_file_attributes&0x400 or not (stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode))
            or (not directory and value.st_nlink!=1)):
        raise AssertionError('regular owned fixture required')
    return value


def _validate_hostile_fixture(*,require_unelevated=True):
    """No symlink following; exact synthetic target and closed fixture topology."""
    if require_unelevated and bool(ctypes.windll.shell32.IsUserAnAdmin()):
        raise AssertionError('production validation must be unelevated')
    if HOSTILE_ROOT.parent != TEMP or str(HOSTILE_ROOT).startswith(str(ROOT)):
        raise AssertionError('external fixture containment mismatch')
    _plain_fixture(HOSTILE_ROOT,True)
    from engineering_orchestration.windows_local_authorization_domain_owner import _current_user_sid,_validate_security_profile
    _validate_security_profile(HOSTILE_ROOT,_current_user_sid(),directory=True)
    marker=HOSTILE_ROOT/'fixture-contract.json'
    if _plain_fixture(marker).st_size>16384:raise AssertionError('fixture marker bound exceeded')
    manifest=json.loads(marker.read_text(encoding='utf-8'))
    if (set(manifest)!= {'contract','root','sha256','volume_guid','known_entries','root_identity','production_invocations'}
            or manifest['contract']!='aio058-hostile-v1' or manifest['root']!=str(HOSTILE_ROOT)
            or manifest['sha256']!=hashlib.sha256(HOSTILE_BYTES).hexdigest()
            or manifest['production_invocations']!=0):
        raise AssertionError('hostile fixture identity mismatch')
    entries=manifest['known_entries']
    if (type(entries) is not list or len(entries)!=len(_fixture_inventory())
            or any(type(item) is not list or len(item)!=2 or type(item[0]) is not str or type(item[1]) is not bool for item in entries)
            or {(text,directory) for text,directory in entries}!=_fixture_inventory()):
        raise AssertionError('hostile fixture inventory mismatch')
    control=_fixture_control().Native()
    try:
        identity=control.identity(HOSTILE_ROOT)
        if [identity[0],identity[1].hex()]!=manifest['root_identity']:
            raise AssertionError('fixture root object substituted')
        target=HOSTILE_ROOT/'owned-target';sentinel=target/'synthetic.bin';repo=HOSTILE_ROOT/'repo'
        for directory in (target,repo,HOSTILE_ROOT/'outside',HOSTILE_ROOT/'evidence',repo/'case-sensitive'):
            _plain_fixture(directory,True)
        if _plain_fixture(sentinel).st_size!=len(HOSTILE_BYTES) or sentinel.read_bytes()!=HOSTILE_BYTES:
            raise AssertionError('synthetic target mismatch')
        for name,destination,is_directory in (('file-link',sentinel,False),('directory-link',target,True)):
            link=repo/name;value=link.lstat()
            if value.st_reparse_tag!=0xA000000C or not stat.S_ISLNK(value.st_mode):
                raise AssertionError('genuine symlink fixture required')
            if bool(value.st_file_attributes&0x10)!=is_directory:raise AssertionError('symlink type mismatch')
            if str(os.readlink(link)) not in (str(destination),'\\\\?\\'+str(destination),'\\??\\'+str(destination)):raise AssertionError('symlink destination mismatch')
        for name,tag,directory in (('junction',0xA0000003,True),('volume-mount',0xA0000003,True),('opaque-reparse',0x42,False)):
            value=(repo/name).lstat()
            if value.st_reparse_tag!=tag or bool(value.st_file_attributes&0x10)!=directory:
                raise AssertionError('genuine reparse identity missing')
        destination=os.readlink(repo/'junction')
        if destination not in (str(target),'\\\\?\\'+str(target),'\\??\\'+str(target)):
            raise AssertionError('junction destination mismatch')
        probe=_fixture_control()
        with control.control_open(repo/'opaque-reparse') as handle:
            query=ctypes.create_string_buffer(16384);transferred=ctypes.c_uint32()
            if not control.kernel.DeviceIoControl(probe.HANDLE(handle.value),0x900a8,None,0,query,len(query),ctypes.byref(transferred),None):
                raise AssertionError('opaque fixture query failed')
            expected=probe.struct.pack('<IHH',probe.CUSTOM_TAG,4,0)+probe.CUSTOM_GUID.bytes_le+b'AIOX'
            if query.raw[:transferred.value]!=expected:raise AssertionError('opaque fixture identity mismatch')
        for name,data in (('case-sensitive/a.bin',b'lower'),('case-sensitive/A.bin',b'UPPER'),('PlainLongName.bin',b'long name')):
            path=repo/name
            if _plain_fixture(path).st_size!=len(data) or path.read_bytes()!=data:
                raise AssertionError('synthetic name fixture mismatch')
        with control.control_open(repo/'case-sensitive',directory=True) as handle:
            if not control.metadata(handle,True).case_sensitive:raise AssertionError('case-sensitive fixture missing')
        short=ctypes.create_unicode_buffer(8192)
        length=control.kernel.GetShortPathNameW(str(repo/'PlainLongName.bin'),short,len(short))
        if not length or length>=len(short) or short.value.rsplit('\\',1)[-1]!='PLAINL~1.BIN':
            raise AssertionError('explicit short alias fixture missing')
        volume=ctypes.create_unicode_buffer(128)
        function=control.kernel.GetVolumeNameForVolumeMountPointW
        function.argtypes,function.restype=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32],ctypes.c_int
        if not function(str(repo/'volume-mount')+'\\',volume,len(volume)) or volume.value!=manifest['volume_guid']:
            raise AssertionError('owned mount topology mismatch')
        _plain_fixture(HOSTILE_ROOT/'evidence/second-owned-volume.vhd')
    finally:
        for handle in tuple(control._handles):handle.close()
    return repo


def cleanup_hostile_fixture():
    """Human-admin teardown of this exact fixture, never a test/reader runner.

    No disk enumeration, recursive removal, policy changes or checkout writes.
    Preflight VHD access and prove volume/device ownership BEFORE unmounting.
    Preserve the contract for a retry after an interrupted storage teardown.
    """
    import re
    if not bool(ctypes.windll.shell32.IsUserAnAdmin()):
        raise AssertionError('Human Administrator fixture cleanup required')
    if HOSTILE_ROOT.parent!=TEMP or str(HOSTILE_ROOT).startswith(str(ROOT)):
        raise AssertionError('fixture cleanup ownership mismatch')
    _plain_fixture(HOSTILE_ROOT,True)
    from engineering_orchestration.windows_local_authorization_domain_owner import _current_user_sid,_validate_security_profile
    _validate_security_profile(HOSTILE_ROOT,_current_user_sid(),directory=True)
    for parent in (HOSTILE_ROOT/'repo',HOSTILE_ROOT/'evidence'):
        _plain_fixture(parent,True)
    marker=HOSTILE_ROOT/'fixture-contract.json'
    if _plain_fixture(marker).st_size>16384:raise AssertionError('fixture marker bound exceeded')
    manifest=json.loads(marker.read_text(encoding='utf-8'))
    if (set(manifest)!={'contract','root','sha256','volume_guid','known_entries','root_identity','production_invocations'}
            or manifest['contract']!='aio058-hostile-v1' or manifest['root']!=str(HOSTILE_ROOT)
            or manifest['sha256']!=hashlib.sha256(HOSTILE_BYTES).hexdigest()
            or manifest['production_invocations']!=0
            or type(manifest['volume_guid']) is not str
            or not re.fullmatch(r'\\\\\?\\Volume\{[0-9a-fA-F-]{36}\}\\',manifest['volume_guid'])):
        raise AssertionError('fixture contract mismatch')
    entries=manifest['known_entries']
    if (type(entries) is not list or len(entries)!=len(_fixture_inventory())
            or any(type(item) is not list or len(item)!=2 or type(item[0]) is not str or type(item[1]) is not bool for item in entries)
            or {(text,directory) for text,directory in entries}!=_fixture_inventory()):
        raise AssertionError('fixture cleanup inventory mismatch')
    mount=HOSTILE_ROOT/'repo/volume-mount'
    image=HOSTILE_ROOT/'evidence/second-owned-volume.vhd'
    _plain_fixture(image)
    # Only these declared objects may be reparses. Do not descend into them.
    reparses={'repo/file-link':(0xA000000C,False),'repo/directory-link':(0xA000000C,True),
        'repo/junction':(0xA0000003,True),'repo/opaque-reparse':(0x42,False)}
    for text,directory in sorted(entries,key=lambda item:len(Path(item[0]).parts)):
        path=Path(text)
        if path==mount or path.parent==mount:continue
        if not os.path.lexists(path):continue  # A prior bounded cleanup may have progressed.
        relative=path.relative_to(HOSTILE_ROOT).as_posix()
        if relative in reparses:
            value=path.lstat();tag,is_directory=reparses[relative]
            if value.st_reparse_tag!=tag or bool(value.st_file_attributes&0x10)!=is_directory:
                raise AssertionError('cleanup reparse identity mismatch')
        else:_plain_fixture(path,directory)
    probe=_fixture_control();control=probe.Native()
    output=probe.HANDLE()
    image_pin=None
    def failure(name,code):
        raise OSError(int(code),name+' failed: Windows error '+str(int(code)))
    try:
        identity=control.identity(HOSTILE_ROOT)
        if [identity[0],identity[1].hex()]!=manifest['root_identity']:
            raise AssertionError('fixture root object substituted')
        image_pin=control.control_open(image,access=probe.FILE_READ_ATTRIBUTES,share=3)
        image_meta=control.metadata(image_pin)
        if image_meta.path!='\\\\?\\'+str(image) or image_meta.tag or image_meta.directory or image_meta.nlink!=1:
            raise AssertionError('exact owned VHD identity unverified')
        disk=ctypes.WinDLL(r'C:\Windows\System32\virtdisk.dll',use_last_error=True)
        disk.OpenVirtualDisk.argtypes,disk.OpenVirtualDisk.restype=[ctypes.POINTER(probe.VIRTUAL_STORAGE_TYPE),ctypes.c_wchar_p,probe.ULONG,probe.ULONG,ctypes.c_void_p,ctypes.POINTER(probe.HANDLE)],probe.ULONG
        disk.GetVirtualDiskPhysicalPath.argtypes,disk.GetVirtualDiskPhysicalPath.restype=[probe.HANDLE,ctypes.POINTER(probe.ULONG),ctypes.c_wchar_p],probe.ULONG
        disk.GetVirtualDiskInformation.argtypes,disk.GetVirtualDiskInformation.restype=[probe.HANDLE,ctypes.POINTER(probe.ULONG),ctypes.c_void_p,ctypes.POINTER(probe.ULONG)],probe.ULONG
        disk.DetachVirtualDisk.argtypes,disk.DetachVirtualDisk.restype=[probe.HANDLE,probe.ULONG,probe.ULONG],probe.ULONG
        class OpenParameters(ctypes.Structure):
            _fields_=[('Version',probe.ULONG),('RWDepth',probe.ULONG)]
        class InfoValue(ctypes.Union):
            _fields_=[('loaded',ctypes.c_int),('abi_union',ctypes.c_uint64*3)]
        class DiskInfo(ctypes.Structure):
            _fields_=[('Version',probe.ULONG),('value',InfoValue)]
        class Extent(ctypes.Structure):
            _fields_=[('number',probe.ULONG),('start',ctypes.c_int64),('length',ctypes.c_int64)]
        class Extents(ctypes.Structure):
            _fields_=[('count',probe.ULONG),('extent',Extent)]
        if ctypes.sizeof(OpenParameters)!=8 or ctypes.sizeof(DiskInfo)!=32 or DiskInfo.value.offset!=8 or ctypes.sizeof(Extents)!=32:
            raise AssertionError('unsupported owned-volume cleanup ABI')
        storage=probe.VIRTUAL_STORAGE_TYPE(2,probe.GUID.from_uuid(probe.uuid.UUID('ec984aec-a0f9-47e9-901f-71415a66345b')))
        parameters=OpenParameters(1,1)
        # GET_INFO | DETACH; the latter is required to reopen permanent attachments.
        error=disk.OpenVirtualDisk(ctypes.byref(storage),str(image),0x000c0000,0,ctypes.byref(parameters),ctypes.byref(output))
        if error:
            output=probe.HANDLE()  # API defines no output handle on failure.
            failure('OpenVirtualDisk exact owned image',error)
        def loaded():
            info=DiskInfo();info.Version=13;size=probe.ULONG(ctypes.sizeof(info));used=probe.ULONG()
            error=disk.GetVirtualDiskInformation(output,ctypes.byref(size),ctypes.byref(info),ctypes.byref(used))
            if error:failure('GetVirtualDiskInformation IS_LOADED',error)
            if info.value.loaded not in (0,1):raise AssertionError('invalid attached-state response')
            return bool(info.value.loaded)
        get_mount=control.kernel.GetVolumeNameForVolumeMountPointW
        get_mount.argtypes,get_mount.restype=[ctypes.c_wchar_p,ctypes.c_wchar_p,probe.ULONG],ctypes.c_int
        def mounted():
            buffer=ctypes.create_unicode_buffer(128);ctypes.set_last_error(0)
            if get_mount(str(mount)+'\\',buffer,len(buffer)):
                if buffer.value!=manifest['volume_guid']:raise AssertionError('foreign volume at owned mount')
                return True
            error=ctypes.get_last_error()
            if error not in (2,3,4390):failure('Query exact owned mount',error)
            return False
        attached=loaded();registered=mounted()
        if os.path.lexists(mount):
            value=mount.lstat()
            if registered:
                if value.st_reparse_tag!=0xA0000003 or os.readlink(mount)!=manifest['volume_guid']:
                    raise AssertionError('owned mount identity mismatch')
            else:_plain_fixture(mount,True)
        if registered and not attached:raise AssertionError('mount/image attachment mismatch')
        if attached:
            physical=ctypes.create_unicode_buffer(128);size=probe.ULONG(ctypes.sizeof(physical))
            error=disk.GetVirtualDiskPhysicalPath(output,ctypes.byref(size),physical)
            if error:failure('GetVirtualDiskPhysicalPath exact image',error)
            if not re.fullmatch(r'\\\\\.\\PhysicalDrive[0-9]{1,6}',physical.value):
                raise AssertionError('invalid owned VHD device mapping')
            number=int(physical.value.rsplit('PhysicalDrive',1)[1])
            volume=control.kernel.CreateFileW(manifest['volume_guid'].rstrip('\\'),0,7,None,3,0,None)
            if not volume or volume==ctypes.c_void_p(-1).value:failure('Open exact owned volume for identity',ctypes.get_last_error())
            try:
                extents=Extents();used=probe.ULONG()
                if not control.kernel.DeviceIoControl(probe.HANDLE(volume),0x560000,None,0,ctypes.byref(extents),ctypes.sizeof(extents),ctypes.byref(used),None):
                    failure('Query exact owned volume extents',ctypes.get_last_error())
                if used.value!=ctypes.sizeof(extents) or extents.count!=1 or extents.extent.number!=number or extents.extent.length<=0:
                    raise AssertionError('volume does not belong to exact owned VHD')
            finally:
                if not control.kernel.CloseHandle(probe.HANDLE(volume)):failure('Close owned volume query handle',ctypes.get_last_error())
            print('EXACT VHD / VOLUME / MOUNT OWNERSHIP: VERIFIED',flush=True)
        if registered:
            if not control.kernel.DeleteVolumeMountPointW(str(mount)+'\\'):
                failure('DeleteVolumeMountPointW exact owned mount',ctypes.get_last_error())
        if mounted():raise AssertionError('owned mount remains registered')
        # Close all other owned image/volume handles before DetachVirtualDisk.
        image_pin.close();image_pin=None
        if attached:
            error=disk.DetachVirtualDisk(output,0,0)
            if error:failure('DetachVirtualDisk exact owned image',error)
        # A successful detach return alone does not prove permanent attachment is gone.
        if loaded():raise AssertionError('owned permanent VHD remains attached; no files deleted')
        if mounted():raise AssertionError('owned mount returned after detach')
        if not control.kernel.CloseHandle(output):failure('Close owned VHD handle',ctypes.get_last_error())
        output=probe.HANDLE()
        if control.identity(image)!=image_meta.identity:raise AssertionError('owned VHD file substituted')
        print('OWNED MOUNT REGISTERED: NO',flush=True)
        print('OWNED VHD ATTACHED: NO',flush=True)
        # Delete reparse objects themselves first; never traverse mounted contents.
        for relative,(tag,directory) in reparses.items():
            path=HOSTILE_ROOT/relative
            if os.path.lexists(path):os.rmdir(path) if directory else os.unlink(path)
        # Keep contract, image, evidence directory and root until all other objects are gone.
        deferred={HOSTILE_ROOT,HOSTILE_ROOT/'evidence',marker,image}
        for text,directory in sorted(entries,key=lambda item:len(Path(item[0]).parts),reverse=True):
            path=Path(text)
            if path in deferred or path.parent==mount or path.relative_to(HOSTILE_ROOT).as_posix() in reparses:continue
            if os.path.lexists(path):
                _plain_fixture(path,directory)
                os.rmdir(path) if directory else os.unlink(path)
        os.unlink(image)
        os.unlink(marker)
        os.rmdir(HOSTILE_ROOT/'evidence')
        os.rmdir(HOSTILE_ROOT)
        if os.path.lexists(HOSTILE_ROOT):raise AssertionError('fixture cleanup incomplete')
        print('SYMLINK/JUNCTION/OPAQUE REPARSE LEFT: NO')
        print('OTHER SYSTEM MOUNTS TOUCHED: NO')
        print('REPOSITORY FILES MODIFIED BY ADMIN STEP: NO')
        print('FIXTURE ROOT CLEANED: YES')
        print('FIXTURE ROOT EXISTS: NO')
    finally:
        if output.value:
            if not control.kernel.CloseHandle(output):failure('Close owned VHD handle on failure',ctypes.get_last_error())
        for handle in tuple(control._handles):handle.close()


def _entry_crash_probe(root_text,path_text,nonce,cut):
    """Closed child storage probe, no native adapter and no new fixture root."""
    import sys
    if bool(ctypes.windll.shell32.IsUserAnAdmin()):raise AssertionError('unelevated storage probe required')
    root=Path(root_text);path=Path(path_text)
    if (root.parent!=TEMP or root.resolve()!=root or not root.name.startswith('aio-056-')
            or root.is_symlink() or root.is_junction() or path!=root/'dispatch.sqlite3'
            or len(nonce)!=64 or (root/'.aio056-owner').read_text(encoding='ascii')!=nonce
            or cut not in ('entry.before_insert','entry.after_insert','entry.after_commit_before_response')):
        raise AssertionError('storage probe containment/nonce/cut mismatch')
    def setup(f):
        f.root,f.nonce,f.configuration=root,nonce,claims.fixture.config_for(path)
        f.sessions=[];f.clock=claims._Clock();f.clock.value=claims.T+timedelta(seconds=31)
    def existing(f,**kwargs):
        f.store=f._open()
        with closing(claims.outbox._connect(path)) as connection:
            row=connection.execute('SELECT * FROM agent_execution_dispatch_admissions').fetchone()
            f.grants=[f.store._admission_from_row(row).grant]
        f.facade=f._facade(f.store)
        return f.facade
    original_claim=claims.DispatchClaimLeaseTests._claim
    def claim(f,number=1,facade=None):return original_claim(f,193,facade)
    with mock.patch.object(claims.DispatchClaimLeaseTests,'setUp',new=setup), \
            mock.patch.object(claims.DispatchClaimLeaseTests,'_setup',new=existing), \
            mock.patch.object(claims.DispatchClaimLeaseTests,'_claim',new=claim), \
            mock.patch.object(claims.adapter._WindowsOwnedAuthorizationDomainSession,'_revalidate',new=claims._raw_revalidate):
        test=unittest.TestCase();r=predecessor._Rig(test);cap=r.cap(test)
        def terminate(point):
            if point==cut:
                print('AIO058_STORAGE_CRASH '+json.dumps(dict(cut=cut,administrator=False,generation=r.claim.lease_generation)),flush=True)
                os._exit(93)  # No finally, rollback, cell cleanup or continuation.
        with mock.patch.object(r.store,'_fault',side_effect=terminate):_enter(r,cap)
        raise AssertionError('required storage termination cut not reached')


class _NativeRig:
    """Genuine Windows owner/Producer/JIT chain; synthetic Run and repository."""
    def __init__(self,test,resource=FIRST_RESOURCE,data=FIRST_BYTES,external=None,hard_link=None):
        from tests import test_local_operational_trust as integrated
        from engineering_orchestration import agent_execution_authorization_grant_producer as producer
        from engineering_orchestration import local_operational_trust as trust
        from engineering_orchestration import _local_dispatch_claim_lease as lease
        from engineering_orchestration import windows_local_authorization_domain_owner as windows
        names=('_IdentityAdapter','_HumanApprovalAdapter','_PolicyDecisionAdapter','_IssuerStateAuthority','_EntitlementPolicy')
        patches=[mock.patch.object(integrated,name,type('Cooperative'+name,(predecessor._Cooperative,getattr(integrated,name)),{})) for name in names]
        for patch in patches:patch.start()
        try:
            self.h=integrated._WindowsHarness(test)
        finally:
            for patch in reversed(patches):patch.stop()
        self.session=self.h.coordinator._session
        self.store=self.session._store
        self.clock=self.h.clock
        self.run=integrated._make_run(resource=resource)
        principal,proof=self.h.human_authority(self.run)
        admitted=self.h.coordinator.admit(run=self.run,authenticated_principal=principal,authority_proof=proof)
        test.assertEqual(admitted.outcome.value,'newly_admitted')
        self.grant=admitted.admission.grant
        self.binding_value=admitted.admission.tool_binding
        self.facade=lease._create_owned_dispatch_claim_lease(self.session)
        self.claim=self.facade.claim(claims.token(1)).claim
        test.assertIsNotNone(self.claim)
        state=self.h.coordinator._producer._state
        facts=predecessor._Facts(self.run)
        self.a=jit._compose_jit_execution_attempt_authorizer(session=self.session,
            producer_binding=producer._new_binding(state),
            resolver=trust._build_native_resolver(runtime_option_id=self.run.contract.runtime_option_id,
                environment_id=self.run.contract.environment_id),current_source=facts)
        test.addCleanup(self.a.close)
        self.subject=self.a.subject(self.claim,self.facade._executor,self.run,self.binding_value)
        self.principal=principal
        now=self.clock.value
        self.decision=self.a.mint_entry_decision(self.subject,principal,
            provenance_reference='aio058-native',approval_session_id='aio058-native',
            valid_from=now-timedelta(seconds=1),valid_until=now+timedelta(minutes=4))
        with self.a.guard.mutation_scope(self.h.human,'proof_mint'):
            self.h.human._minted[id(self.decision)]=self.decision
        self.repo=external or self.h.root.parent/'repo'
        if external is None:
            self.repo.mkdir()
            windows._apply_security_profile(self.repo,windows._current_user_sid(),directory=True)
            components=native._resource_components(resource)
            if data is not None:
                target=self.repo.joinpath(*components)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
                if hard_link is not None:
                    if hard_link not in ('inside','outside'):
                        raise AssertionError('unknown hard-link fixture location')
                    alias=(self.h.root.parent if hard_link=='outside' else target.parent)/'alias.bin'
                    os.link(target,alias)
        self.root=native._provision_trusted_root(session=self.session,
            environment_id=self.run.contract.environment_id,path=self.repo)
        test.addCleanup(self.root.close)
        self.coordinator=entry._ControlledInvocationCoordinator(self.a,self.root)

    def cap(self,test):
        result=self.a.prepare(self.subject,self.principal,self.decision)
        test.assertEqual(result.outcome,'prepared',result)
        return result.capability

    def invoke(self,test):
        return self.coordinator.invoke(self.cap(test),self.principal,self.decision)


class ProductionScenarios(unittest.TestCase):
    _assert_sec_057_3 = predecessor.FoundationTests._assert_sec_057_3
    def rig(self, **kwargs):
        return predecessor._Rig(self,**kwargs)

    def asserted_entry(self,r):
        cap=r.cap(self)
        result=_enter(r,cap)
        self.assertEqual(result.outcome,'entered',result)
        self.assertEqual(_count(r),1)
        self.assertEqual(cap._cell.state,'CONSUMED')
        return cap,result.entry

    def run_scenario(self, scenario):
        group,n=scenario[0],int(scenario[1:])
        method=getattr(self,'group_'+group)
        method(n)

    def group_A(self,n):
        r=self.rig()
        if n==10:
            for error in (store_module.SqliteAdmissionStoreIncompatibleSchemaError('v3'),OSError('unavailable')):
                other=self.rig();cap=other.cap(self)
                with mock.patch.object(other.store,'_open_existing',side_effect=error):
                    with self.assertRaises(type(error)):_enter(other,cap)
                self.assertNotEqual(_history(other,cap).outcome,'verified_absent')
                self.assertEqual(_count(other),0)
            cap=r.cap(self)
            with closing(_connect(r)) as c:c.execute('PRAGMA user_version=3')
            with self.assertRaises(store_module.SqliteAdmissionStoreIncompatibleSchemaError):_enter(r,cap)
            self.assertEqual(_count(r),0)
            return
        cap,e=self.asserted_entry(r)
        if n in (1,2,3,4):
            self.assertEqual(e.identity,r.claim.identity)
            self.assertEqual((e.claim_id,e.executor_instance_id,e.lease_generation),
                (r.claim.claim_id,r.claim.executor_instance_id,r.claim.lease_generation))
            self.assertNotIn('entry_id',{f.name for f in fields(e)})
            with closing(_connect(r)) as c:
                columns=[row['name'] for row in c.execute('PRAGMA table_info(agent_execution_entries)')]
                self.assertEqual(len(columns),9)
                self.assertFalse(any('json' in name for name in columns))
            self.assertEqual(e.entry_time,r.store.watermark()[0])
        elif n in (5,6,7):
            with closing(_connect(r)) as c:
                row=tuple(c.execute('SELECT * FROM agent_execution_entries').fetchone())
                for sql,values in (
                    ('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row),
                    ('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',(*row[:4],claims.token(999),*row[5:])),
                    ('INSERT OR REPLACE INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row),
                    ('INSERT OR IGNORE INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row),
                    ('UPDATE agent_execution_entries SET claim_id=?',(claims.token(999),)),
                    ('DELETE FROM agent_execution_entries',()),
                ):
                    with self.subTest(sql=sql):
                        with self.assertRaises(sqlite3.IntegrityError):
                            c.execute(sql,values)
            self.assertEqual(_count(r),1)
        else:
            self.assertEqual(_history(r,cap).entry,e)
            self.assertTrue(_history(r,cap).history_only)
            self.assertEqual(_enter(r,cap).outcome,'terminal_capability')
            self.assertEqual(_count(r),1)

    def group_B(self,n):
        if n==6:
            self.final_prerequisite_branches()
            return
        if n==2:
            self.no_target_before_acknowledged_commit()
            return
        if n==10:
            self.writer_and_cell_release_order()
            return
        r=self.rig(short_grant=n==5)
        cap=r.cap(self)
        if n==3:
            r.clock.value=claims.T+timedelta(seconds=30)
            self.assertEqual(_enter(r,cap).outcome,'expired_claim')
            self.assertEqual(_count(r),0)
        elif n==4:
            def expire(point):
                if point=='entry.before_commit':
                    r.clock.value=claims.T+timedelta(minutes=6)
            with mock.patch.object(r.store,'_fault',side_effect=expire):
                self.assertEqual(_enter(r,cap).outcome,'entered')
            self.post_entry_survival(before_commit_expire=True)
        elif n==5:
            r.clock.value=claims.T+timedelta(seconds=2)
            self.assertEqual(_enter(r,cap).outcome,'entered')
            self.final_authority_branches()
        elif n==7:
            before=r.clock.calls
            self.assertEqual(_enter(r,cap).outcome,'entered')
            self.assertEqual(r.clock.calls,before+1)
            for value in (claims.T-timedelta(microseconds=1),None,'bad',claims.T.replace(tzinfo=None),object()):
                other=self.rig()
                other_cap=other.cap(self)
                other.clock.value=value
                self.assertNotEqual(_enter(other,other_cap).outcome,'entered')
                self.assertEqual(_count(other),0)
        elif n==8:
            other=self.rig()
            with other.a.session.operation():
                with other.a.guard.read_scope():
                    subject=cap._cell.subject
                    request=store_module._mint_dispatch_request('query',r.session,r.store,
                        capability=subject.executor,claim_id=subject.claim_id,identity=subject.dispatch_identity,
                        generation=subject.lease_generation,mode='current')
                    result=other.store._enter_execution(request,entry._EntryOperation(r.a,cap._cell,r.principal,r.decision))
            self.assertNotEqual(result.outcome,'entered')
            self.assertEqual(_count(other),0)
        elif n==9:
            for cut in ('entry.after_insert','entry.after_watermark','entry.before_commit'):
                other=self.rig(); other_cap=other.cap(self)
                before=other.store.watermark()
                def fail(point):
                    if point==cut: raise OSError('synthetic cut')
                with mock.patch.object(other.store,'_fault',side_effect=fail):
                    result=_enter(other,other_cap)
                self.assertNotEqual(result.outcome,'entered')
                self.assertEqual(_count(other),0)
                self.assertEqual(other.store.watermark(),before)
        else:
            if n==1:
                copied=copy.copy(cap._cell)
                with r.session.operation():
                    with r.a.guard.read_scope():
                        subject=cap._cell.subject
                        request=store_module._mint_dispatch_request('query',r.session,r.store,
                            capability=subject.executor,claim_id=subject.claim_id,identity=subject.dispatch_identity,
                            generation=subject.lease_generation,mode='current')
                        result=r.store._enter_execution(request,entry._EntryOperation(r.a,copied,r.principal,r.decision))
                self.assertEqual(result.outcome,'invalid_capability')
                self.assertEqual(_count(r),0)
                self.assertEqual(cap._cell.state,'PREPARED')
            trace=[]
            def observe(point):
                trace.append(point)
                self.assertEqual(cap._cell.state,'PREPARED' if point=='entry.after_begin' else 'CONSUMING')
            with mock.patch.object(r.store,'_fault',side_effect=observe):
                self.assertEqual(_enter(r,cap).outcome,'entered')
            self.assertEqual(trace, ['entry.after_begin','entry.before_insert','entry.after_insert',
                'entry.after_watermark','entry.before_commit','entry.after_commit_before_response'])
            self.assertEqual(cap._cell.state,'CONSUMED')

    def no_target_before_acknowledged_commit(self):
        for cut in ('entry.after_begin','entry.before_insert','entry.after_insert',
                'entry.after_watermark','entry.before_commit','entry.after_commit_before_response'):
            with self.subTest(cut=cut):
                r=_NativeRig(self);cap=r.cap(self)
                def fail(point):
                    if point==cut:raise OSError('synthetic unacknowledged Entry')
                with mock.patch.object(r.store,'_fault',side_effect=fail), \
                        mock.patch.object(r.root._native,'open_component',side_effect=AssertionError('target open before Entry ack')) as opening, \
                        mock.patch.object(r.root._native,'metadata',side_effect=AssertionError('target metadata before Entry ack')) as metadata, \
                        mock.patch.object(r.root._native,'read_data',side_effect=AssertionError('target content before Entry ack')) as reading:
                    result=r.coordinator.invoke(cap,r.principal,r.decision)
                for intercepted in (opening,metadata,reading):intercepted.assert_not_called()
                self.assertNotEqual(result.entry_result.outcome,'entered');self.assertIsNone(result.invocation)
                self.assertIsNone(r.coordinator._original)
                self.assertEqual(_count(r),int(cut=='entry.after_commit_before_response'))

    def writer_and_cell_release_order(self):
        r=self.rig();cap=r.cap(self);original=r.store._open_existing;closed=[];acknowledged=[]
        class Connection:
            def __init__(self,connection):self.connection=connection
            def __getattr__(self,name):return getattr(self.connection,name)
            def close(self):
                self.assert_once_closed()
                self.connection.close()
            def assert_once_closed(self):
                self_case.assertEqual(cap._cell.state,'CONSUMING')
                self_case.assertFalse(cap._cell.lock.acquire(blocking=False),'C released before connection cleanup')
                closed.append(True)
        self_case=self
        def open_connection(**kwargs):
            connection=original(**kwargs)
            return Connection(connection) if getattr(r.a.guard.thread,'read',False) else connection
        def confirm(point):
            if point=='entry.after_commit_before_response':
                with closing(_connect(r)) as c:c.execute('BEGIN IMMEDIATE');c.execute('ROLLBACK')
                acknowledged.append(True)
                self.assertEqual(closed,[]);self.assertEqual(cap._cell.state,'CONSUMING')
        with mock.patch.object(r.store,'_open_existing',side_effect=open_connection),mock.patch.object(r.store,'_fault',side_effect=confirm):
            self.assertEqual(_enter(r,cap).outcome,'entered')
        self.assertEqual(acknowledged,[True]);self.assertEqual(closed,[True]);self.assertEqual(cap._cell.state,'CONSUMED')
        self.assertTrue(cap._cell.lock.acquire(blocking=False));cap._cell.lock.release()

    def final_authority_branches(self):
        for issuer_kind in ('human','policy'):
            for attack in ('issuer_disabled','issuer_reenabled','principal_invalid','principal_epoch',
                    'decision_invalid','decision_epoch','wrong_subject','issuance_purpose','denied','stale'):
                if attack=='denied' and issuer_kind!='policy':continue
                with self.subTest(issuer=issuer_kind,attack=attack):
                    r=self.rig(issuer_kind=issuer_kind);cap=r.cap(self)
                    if attack=='issuer_disabled':r.issuer.disable()
                    elif attack=='issuer_reenabled':r.issuer.disable();r.issuer.enable()
                    elif attack.startswith('principal'):
                        r.identity.change('principal_invalidate' if attack.endswith('invalid') else 'epoch_revision',
                            **({'valid':False} if attack.endswith('invalid') else {'epoch':object()}))
                    elif attack.startswith('decision'):
                        source=r.human if issuer_kind=='human' else r.policy
                        source.change('decision_invalidate' if attack.endswith('invalid') else 'epoch_revision',
                            **({'valid':False} if attack.endswith('invalid') else {'epoch':object()}))
                    elif attack=='wrong_subject':
                        with r.a.guard.mutation_scope(r.human if issuer_kind=='human' else r.policy,'proof_subject'):
                            record=r.a.state.jit_entry_proofs[id(r.decision)]
                            r.a.state.jit_entry_proofs[id(r.decision)]=(record[0],replace(r.subject,
                                run=replace(r.run,run_id='foreign')),record[2],record[3])
                    else:
                        args=dict(provenance_reference='aio058-failed-authority',valid_from=claims.T-timedelta(seconds=1),
                            valid_until=claims.T+timedelta(minutes=5))
                        if issuer_kind=='human':args['approval_session_id']='aio058-failed-authority'
                        else:args.update(decision='deny' if attack=='denied' else 'allow',policy_revision='aio058-failed-authority')
                        if attack=='issuance_purpose':
                            source=r.human if issuer_kind=='human' else r.policy
                            r.decision=source.mint(principal=r.principal,run=r.run,**args)
                        else:
                            if attack=='stale':args['valid_until']=claims.T
                            r.decision=r.a.mint_entry_decision(r.subject,r.principal,**args)
                    self.assertNotEqual(_enter(r,cap).outcome,'entered')
                    self.assertEqual(_count(r),0)

    def final_prerequisite_branches(self):
        q=predecessor.prereqs
        attacks=[('candidate_result','malformed'),('requirement','malformed'),('capability_result','malformed'),
            ('permission_result','malformed'),('authorization_result','malformed'),
            ('candidate_result','blocked'),('candidate_result','unknown'),('capability_result','absent'),
            ('capability_result','unknown'),('permission_result','denied'),('permission_result','unknown'),
            ('authorization_result','denied'),('authorization_result','unknown')]
        attacks += [(kind,'mismatch:'+field) for kind,fields_ in (
            ('candidate_result',('responsibility_key','actor_id','runtime_option_id','option_id')),
            ('requirement',('operation_id','resource')),
            ('capability_result',('runtime_option_id','operation_id')),
            ('permission_result',('runtime_option_id','environment_id','operation_id','resource')),
            ('authorization_result',('actor_id','runtime_option_id','option_id','environment_id','operation_id','resource')))
            for field in fields_]
        attacks += [('mode',name) for name in ('actual_mismatch','actual_malformed','required_malformed')]
        for kind,attack in attacks:
            with self.subTest(kind=kind,attack=attack):
                r=self.rig();cap=r.cap(self);values=dict(r.facts.inputs)
                with r.a.guard.mutation_scope(r.facts,'prerequisites'):
                    if kind=='mode':
                        if attack=='actual_mismatch':r.facts.actual_mode='lite'
                        elif attack=='actual_malformed':r.facts.actual_mode=object()
                        else:r.facts.required_mode=object()
                    elif attack=='malformed':values[kind]=object()
                    elif attack.startswith('mismatch:'):
                        field=attack.split(':')[1];value=values[kind]
                        attribute='normalized_observations' if kind in ('permission_result','capability_result') else 'normalized_evidence'
                        if kind in ('candidate_result','requirement'):subject=value
                        else:subject=getattr(value,attribute)[0]
                        original=getattr(subject,field)
                        changed=replace(subject,**{field:tuple('foreign' for _ in original) if type(original) is tuple else original+'-foreign'})
                        values[kind]=changed if kind in ('candidate_result','requirement') else replace(value,**{attribute:(changed,)})
                    elif kind=='candidate_result':
                        value=values[kind]
                        values[kind]=replace(q.candidate(q.AgentExecutionCandidatePrerequisiteOutcome.BLOCKED if attack=='blocked'
                            else q.AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,actor_id=value.actor_id,
                            runtime_option_id=value.runtime_option_id,option_id=value.option_id),responsibility_key=value.responsibility_key)
                    elif kind=='capability_result':
                        values[kind]=q.capability(q.RuntimeOperationCapabilityState.ABSENT if attack=='absent'
                            else q.RuntimeOperationCapabilityState.UNKNOWN,runtime_option_id=r.run.contract.runtime_option_id)
                    elif kind=='permission_result':
                        values[kind]=q.permission(q.EnvironmentOperationPermissionState.DENIED if attack=='denied'
                            else q.EnvironmentOperationPermissionState.UNKNOWN,runtime_option_id=r.run.contract.runtime_option_id,
                            environment_id=r.run.contract.environment_id,resource=r.run.contract.resource)
                    else:
                        value=values[kind].normalized_evidence[0]
                        values[kind]=q.authorization(q.AgentExecutionAuthorizationState.DENIED if attack=='denied'
                            else None,responsibility_key=(value.task_id,value.workflow_id,value.stage_id,value.role_id),
                            actor_id=value.actor_id,runtime_option_id=value.runtime_option_id,option_id=value.option_id,
                            environment_id=value.environment_id,resource=value.resource)
                    r.facts.inputs=values
                self.assertNotEqual(_enter(r,cap).outcome,'entered')
                self.assertEqual(_count(r),0)

    def group_C(self,n):
        r=self.rig(); cap=r.cap(self)
        if n==1:
            _new_generation(r,self)
            self.assertEqual(_enter(r,cap).outcome,'stale_generation')
            self.assertEqual(_count(r),0)
        else:
            self.assertEqual(_enter(r,cap).outcome,'entered')
            if n==6:
                r.clock.value=claims.T+timedelta(seconds=5)
                self.assertEqual(r.fixture._renew(r.claim).outcome,'newly_renewed')
                r.clock.value=claims.T+timedelta(seconds=36)
            newer=_new_generation(r,self)
            self.assertEqual(_enter(r,newer).outcome,'already_entered')
            self.assertEqual(_count(r),1)
            self.assertEqual(_history(r,cap).outcome,'historical_entry')
            self.assertEqual(r.fixture._open().watermark(),r.store.watermark())
            if n==5:
                with closing(_connect(r)) as c:
                    pk=tuple(row['name'] for row in c.execute('PRAGMA table_info(agent_execution_entries)') if row['pk'])
                    self.assertEqual(pk,('authorization_domain_id','issuer_kind','issuer_id','grant_id'))

    def group_D(self,n):
        r=self.rig();cap=r.cap(self)
        committed=n in (1,3,5)
        if n in (2,6):
            with mock.patch.object(store_module,'_commit',side_effect=store_module._CommitUnknown('synthetic commit unknown rollback')):
                result=_enter(r,cap)
            self.assertEqual(result.outcome,'commit_unknown')
        else:
            cut='entry.after_commit_before_response' if committed else 'entry.before_commit'
            def fail(point):
                if point==cut:raise OSError('synthetic interrupted response')
            with mock.patch.object(r.store,'_fault',side_effect=fail):result=_enter(r,cap)
        self.assertNotEqual(result.outcome,'entered')
        self.assertIn(cap._cell.state,('UNCERTAIN','REJECTED'))
        historical=_history(r,cap)
        self.assertEqual(historical.outcome,'historical_entry' if committed else 'verified_absent')
        self.assertTrue(historical.history_only)
        self.assertEqual(_enter(r,cap).outcome,'terminal_capability')
        if n==5:
            foreign=self.rig();other=foreign.cap(self)
            with foreign.session.operation():
                with foreign.a.guard.read_scope():
                    subject=cap._cell.subject
                    request=store_module._mint_dispatch_request('query',r.session,r.store,capability=subject.executor,
                        claim_id=subject.claim_id,identity=subject.dispatch_identity,generation=subject.lease_generation,mode='current')
                    self.assertNotEqual(foreign.store._classify_execution_entry(request).outcome,'historical_entry')
            self.assertEqual(_count(foreign),0)
        if n==6:
            newer=_new_generation(r,self)
            self.assertEqual(_enter(r,newer).outcome,'entered')
            self.assertEqual(_enter(r,cap).outcome,'terminal_capability')
            occupied=self.rig();old,e=self.asserted_entry(occupied)
            new=_new_generation(occupied,self)
            self.assertEqual(_enter(occupied,new).outcome,'already_entered')
            self.assertEqual(_count(occupied),1)

    def group_E(self,n):
        if n in (3,4,10):
            for action in (lambda:entry._Continuation(),lambda:copy.copy(object.__new__(entry._Continuation)),
                    lambda:copy.deepcopy(object.__new__(entry._Continuation)),
                    lambda:pickle.dumps(object.__new__(entry._Continuation))):
                with self.assertRaises(TypeError):action()
            with self.assertRaises(TypeError):native._invoke_repository_file_read(object(),object(),FIRST_RESOURCE)
        r=_NativeRig(self)
        cap=r.cap(self)
        other_executor=claims.adapter._create_owned_dispatch_claim_lease(r.session)._executor if n==5 else None
        captured=[]
        def inspect(cell):
            original=r.coordinator._original
            captured.append(original)
            self.assertIs(original._cell,cap._cell)
            self.assertIs(original._root,r.root)
            self.assertEqual(original._entry.identity,r.claim.identity)
            self.assertTrue(r.a.guard.thread.read)
            self.assertEqual(_count(r),1)
            if n in (2,6):
                with r.a.guard.leaf():
                    r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
                    with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
            elif n==5:
                for field,value in (('_pid',-1),('_authorizer_epoch',object()),('_guard_epoch',object()),
                        ('_frame',object()),('_root',object()),('_entry',copy.copy(original._entry)),
                        ('_cell',copy.copy(original._cell)),('_run',copy.copy(original._run)),
                        ('_binding',copy.copy(original._binding))):
                    saved=getattr(original,field)
                    object.__setattr__(original,field,value)
                    try:
                        with r.a.guard.leaf():
                            with self.assertRaises((jit._JitFailure,AttributeError)):
                                r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
                    finally:object.__setattr__(original,field,saved)
                with r.a.guard.leaf():
                    with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,'fixtures/wrong-resource.bin')
                    subject=cell.subject
                    cell.subject=replace(subject,executor=other_executor,executor_id=other_executor._executor_id)
                    try:
                        with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
                    finally:cell.subject=subject
                    saved=r.root._session
                    object.__setattr__(r.root,'_session',object())
                    try:
                        with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
                    finally:object.__setattr__(r.root,'_session',saved)
                errors=[]
                def foreign():
                    try:r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
                    except jit._JitFailure:errors.append(True)
                worker=Thread(target=foreign);worker.start();worker.join(5)
                self.assertFalse(worker.is_alive());self.assertEqual(errors,[True])
            elif n==4:
                for action in (copy.copy,copy.deepcopy,pickle.dumps):
                    with self.assertRaises(TypeError):action(original)
            elif n==3:
                forged=object.__new__(entry._Continuation)
                with self.assertRaises((jit._JitFailure,AttributeError)):
                    r.coordinator._begin_native(forged,r.root,FIRST_RESOURCE)
            elif n==9:
                r.a.guard.closed=True
                raise jit._JitFailure('guard_lost')
            return False  # Mechanics test: suppress adapter, zero target effects.
        with mock.patch.object(r.coordinator,'_availability',side_effect=inspect):
            result=r.coordinator.invoke(cap,r.principal,r.decision)
        self.assertEqual(result.entry_result.outcome,'entered')
        self.assertEqual(result.invocation.reason,'guard_lost' if n==9 else 'adapter_unavailable')
        self.assertIsNone(result.invocation.data)
        self.assertEqual(r.coordinator.history(cap).outcome,'historical_entry')
        for original in captured:
            with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)
        self.assertIsNone(r.coordinator._original)
        self.assertNotEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'entered')
        if n==7:
            r.root.close();r.a.close();r.h.restart()
            reopened=r.h.coordinator._session._store
            reopened.verified_settings()
            self.assertEqual(_count(r),1)
            self.assertNotEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'entered')
            for original in captured:
                with self.assertRaises(jit._JitFailure):r.coordinator._begin_native(original,r.root,FIRST_RESOURCE)

    def _native_read(self,resource='fixtures/plain.bin',data=b'AIO058',external=None,check=None):
        self.assertFalse(bool(ctypes.windll.shell32.IsUserAnAdmin()))
        r=_NativeRig(self,resource,data,external)
        cap=r.cap(self)
        if check is None:
            result=r.coordinator.invoke(cap,r.principal,r.decision)
        else:
            result=check(r,cap)
        self.assertEqual(result.entry_result.outcome,'entered',result)
        self.assertEqual(_count(r),1)
        self.assertIsNone(r.coordinator._original)
        self.assertEqual(len(r.root._native.handles),len(r.root._state.handles))
        return r,result

    def group_I(self,n):
        if n in (1,2,3):
            variants={1:(('fixtures/nested/plain.bin',b'AIO058'),),
                2:(('fixtures/empty.bin',b''),('fixtures/binary.bin',b'\x00\xff\x01'),
                   ('fixtures/invalid-utf8.bin',b'\xc3\x28'),('fixtures/bom-newline.bin',b'\xef\xbb\xbf\r\n')),
                3:(('fixtures/boundary.bin',b'A'*65536),('fixtures/oversize.bin',b'A'*65537))}[n]
            for resource,data in variants:
                with self.subTest(resource=resource):
                    r,outcome=self._native_read(resource,data)
                    if len(data)>65536:
                        self.assertEqual(outcome.invocation.reason,'size_limit_exceeded')
                        self.assertIsNone(outcome.invocation.data)
                    else:
                        self.assertEqual(outcome.invocation.status,'completed')
                        self.assertEqual(outcome.invocation.data,data)
        elif n==4:
            for resource,directory in (('missing-dir/file.bin',False),('fixtures/missing.bin',False),('fixtures/dir',True)):
                r=_NativeRig(self,resource,None)
                if directory:(r.repo/'fixtures/dir').mkdir(parents=True)
                outcome=r.invoke(self)
                self.assertIsNone(outcome.invocation.data)
                self.assertIn(outcome.invocation.reason,('resource_missing','read_failure','containment_rejected'))
        elif n==5:
            for resource in ('a:stream','C:file.bin','C:/file.bin','//server/share/file.bin',
                    '\\\\server\\share','\\\\?\\C:\\file.bin','\\\\.\\pipe\\aio058',
                    'CON','con.txt','COM1.txt','LPT9','fixtures/AUX.bin','COM\u00b9.bin','LPT\u00b2.txt','COM\u00b3.txt'):
                with self.subTest(resource=resource):
                    with self.assertRaises(native._NativeFailure):native._resource_components(resource)
        elif n==6:
            for resource in ('fixtures/plain.bin.','fixtures/plain.bin '):
                with self.assertRaises(native._NativeFailure):native._resource_components(resource)
            r=_NativeRig(self,'fixtures/Plain.bin',None)
            (r.repo/'fixtures').mkdir();(r.repo/'fixtures/plain.bin').write_bytes(b'plain')
            outcome=r.invoke(self);self.assertIsNone(outcome.invocation.data)
            external=_validate_hostile_fixture()
            for resource,expected in (('case-sensitive/a.bin',b'lower'),('case-sensitive/A.bin',b'UPPER'),('PLAINL~1.BIN',None)):
                _,outcome=self._native_read(resource,None,external)
                if expected is None:self.assertIsNone(outcome.invocation.data)
                else:self.assertEqual(outcome.invocation.data,expected)
            for resource,data in (('fixtures/caf\u00e9.bin',b'NFC'),('fixtures/cafe\u0301.bin',b'NFD')):
                _,outcome=self._native_read(resource,data)
                self.assertEqual(outcome.invocation.data,data)
        elif n in (7,8,9):
            self.substitution_races(n)
        elif n in (10,11):
            external=_validate_hostile_fixture()
            resources={10:('file-link','directory-link/synthetic.bin'),
                11:('junction/synthetic.bin','volume-mount/sentinel.bin','opaque-reparse')}[n]
            for resource in resources:
                with self.subTest(resource=resource):
                    _,outcome=self._native_read(resource,None,external)
                    self.assertEqual(outcome.invocation.reason,'containment_rejected')
                    self.assertIsNone(outcome.invocation.data)
        elif n==12:
            for outside in (False,True):
                r=_NativeRig(self,'fixtures/hardlink.bin',b'known',hard_link='outside' if outside else 'inside')
                outcome=r.invoke(self)
                self.assertEqual(outcome.invocation.reason,'containment_rejected')
                self.assertIsNone(outcome.invocation.data)
        elif n==13:
            probe=_fixture_control()
            for access in (probe.FILE_WRITE_DATA,probe.DELETE):
                r=_NativeRig(self,'fixtures/conflict.bin',b'known')
                control=probe.Native()
                with control.control_open(r.repo/'fixtures/conflict.bin',access=access,share=7):
                    outcome=r.invoke(self)
                    self.assertEqual(outcome.invocation.reason,'containment_rejected')
                    self.assertIsNone(outcome.invocation.data)
                with control.control_open(r.repo/'fixtures/conflict.bin',access=access,share=7):pass
        elif n==14:
            self.mapping_exclusion()
        elif n==15:
            self.mutation_races()
        elif n==16:
            self.native_metadata_faults()
        elif n==17:
            self.assertEqual(len(native._resource_components('/'.join(['seg']*15+['file.bin']))),16)
            self.assertEqual(len(native._resource_components('u'*4096)[0]),4096)
            for resource in ('/'.join(['seg']*16+['file.bin']),'u'*4097,'fixtures/\ud800.bin'):
                with self.assertRaises(native._NativeFailure):native._resource_components(resource)
            _,outcome=self._native_read('/'.join(['seg']*15+['file.bin']),b'sixteen')
            self.assertEqual(outcome.invocation.data,b'sixteen')
        else:
            self.native_delay_cleanup()

    def native_metadata_faults(self):
        self.native_profile(6)

    def native_delay_cleanup(self):
        import time
        r=_NativeRig(self,'fixtures/delay.bin',b'known')
        original=r.root._native.call
        reached=[]
        def delayed(name,*args,**kwargs):
            if name=='NtReadFile' and not reached:
                self.assertTrue(r.a.guard.thread.read)
                self.assertTrue(r.root._state.operations)
                time.sleep(.02)
                reached.append(True)
            return original(name,*args,**kwargs)
        with mock.patch.object(r.root._native,'call',side_effect=delayed):outcome=r.invoke(self)
        self.assertEqual(outcome.invocation.data,b'known');self.assertEqual(reached,[True])
        self.assertEqual(len(r.root._native.handles),len(r.root._state.handles))
        self.native_profile(5)
        r=_NativeRig(self,'fixtures/cleanup.bin',b'known')
        original_close=native._Handle.close
        failed=[]
        def close(handle):
            if handle.native is r.root._native and handle not in r.root._state.handles and not failed:
                failed.append(handle)
                raise native._NativeFailure('read_failure')
            return original_close(handle)
        with mock.patch.object(native._Handle,'close',new=close):outcome=r.invoke(self)
        self.assertEqual(outcome.invocation.status,'ambiguous');self.assertIsNone(outcome.invocation.data)
        self.assertEqual(len(failed),1);self.assertEqual(r.root._state.quarantined,failed)
        self.assertFalse(r.root._available(r.session,r.run.contract.environment_id))
        r.root.close()
        self.assertTrue(r.root._closed);self.assertEqual(r.root._native.handles,set())

    def native_profile(self,n):
        if n==2:
            r=_NativeRig(self)
            with self.assertRaises(native._NativeFailure):
                native._provision_trusted_root(session=r.session,environment_id=r.run.contract.environment_id,path=r.repo)
            cap=r.cap(self)
            r.coordinator._reader=lambda *args:None
            result=r.coordinator.invoke(cap,r.principal,r.decision)
            self.assertEqual(result.invocation.reason,'adapter_unavailable')
            self.assertEqual(_count(r),1)
        elif n==6:
            changes=(('identity',(0,b'X'*16)),('identity','malformed_file_id'),('file_type',3),('directory',True),
                ('delete_pending',True),('tag',0x42),('nlink',2),('size',-1))
            for attribute,value in changes:
                r=_NativeRig(self,'fixtures/fault.bin',b'known')
                original=r.root._native.metadata
                def change(handle,directory=False):
                    result=original(handle,directory)
                    changed=(result.identity[0],bytes(16)) if value=='malformed_file_id' else value
                    return replace(result,**{attribute:changed}) if not directory else result
                with mock.patch.object(r.root._native,'metadata',side_effect=change):
                    outcome=r.invoke(self)
                self.assertIsNone(outcome.invocation.data)
            r=_NativeRig(self,'fixtures/fault.bin',b'known')
            with mock.patch.object(r.root._native,'info',side_effect=native._NativeFailure('read_failure')):
                outcome=r.invoke(self)
            self.assertIsNone(outcome.invocation.data)
        elif n==5:
            for fault in ('short','failure'):
                r=_NativeRig(self,'fixtures/fault.bin',b'known')
                original=r.root._native.read_data
                def broken(handle,offset,count,budget):
                    result=original(handle,offset,count,budget)
                    if fault=='short':return result[:-1]
                    raise native._NativeFailure('read_failure')
                with mock.patch.object(r.root._native,'read_data',side_effect=broken):outcome=r.invoke(self)
                self.assertEqual(outcome.invocation.reason,'read_failure')
                self.assertIsNone(outcome.invocation.data)
        elif n==4:
            r=_NativeRig(self,'fixtures/boundary.bin',b'A'*65536)
            requests=[];original=r.root._native.read_data
            def count(handle,offset,size,budget):
                requests.append(size);return original(handle,offset,size,budget)
            with mock.patch.object(r.root._native,'read_data',side_effect=count):outcome=r.invoke(self)
            self.assertEqual(outcome.invocation.data,b'A'*65536)
            self.assertEqual(len(requests),17);self.assertEqual(sum(requests),65537)
        else:
            _,outcome=self._native_read()
            self.assertEqual(outcome.invocation.data,b'AIO058')

    def native_fault(self,n):
        if n in (4,5):
            class Interruption(BaseException):pass
            methods=('open_component','metadata','read_data') if n==4 else ('read_data',)
            for method in methods:
                with self.subTest(cut=method):
                    r=_NativeRig(self,'fixtures/fault.bin',b'known');cap=r.cap(self)
                    original=getattr(r.root._native,method);reached=[]
                    def interrupt(*args,**kwargs):
                        value=original(*args,**kwargs)
                        reached.append(True)
                        # Preserve handle ownership even when the open's caller
                        # never receives its return value (simulated fatal unwind).
                        if method=='open_component':
                            r.root._state.quarantined.append(value);r.root._state.closing=True
                        raise Interruption()
                    with mock.patch.object(r.root._native,method,side_effect=interrupt):
                        with self.assertRaises(Interruption):r.coordinator.invoke(cap,r.principal,r.decision)
                    self.assertEqual(reached,[True]);self.assertEqual(_count(r),1)
                    self.assertEqual(cap._cell.state,'CONSUMED');self.assertIsNone(r.coordinator._original)
                    self.assertEqual(r.coordinator.history(cap).outcome,'historical_entry')
                    r.root.close();r.a.close();r.h.restart()
                    r.h.coordinator._session._store.verified_settings()
                    self.assertEqual(_count(r),1)
                    self.assertNotEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'entered')
            return
        r=_NativeRig(self,'fixtures/fault.bin',b'known');cap=r.cap(self)
        original=type(r.session)._revalidate
        def lose_after(session):
            if session is r.session and _count(r)==1 and r.coordinator._once=='finished':
                raise claims.adapter.AuthorizationDomainOwnershipIntegrityError('synthetic post-effect loss')
            return original(session)
        with mock.patch.object(type(r.session),'_revalidate',new=lose_after):
            result=r.coordinator.invoke(cap,r.principal,r.decision)
        self.assertEqual(result.invocation.status,'ambiguous');self.assertIsNone(result.invocation.data)
        self.assertEqual(_count(r),1)
        self.assertNotEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'entered')

    def _at_cut(self,r,cap,cut,attack):
        """Deterministic test barrier at each native cut; production has no hooks."""
        engine=r.root._native
        opening,metadata,reading=engine.open_component,engine.metadata,engine.read_data
        reached=[]
        def trigger():
            if not reached:
                reached.append(True)
                failures=[]
                def mutate():
                    try:attack()
                    except BaseException as error:failures.append(error)
                worker=Thread(target=mutate);worker.start();worker.join(5)
                self.assertFalse(worker.is_alive(),'bounded fixture mutation did not finish')
                if failures:raise failures[0]
        def open_at(component,parent=None,directory=False):
            if cut=='before_component_open':trigger()
            value=opening(component,parent,directory)
            if cut=='after_ancestor_pin' and directory:trigger()
            return value
        def metadata_at(handle,directory=False):
            if cut=='after_final_open_before_metadata' and not directory:trigger()
            return metadata(handle,directory)
        def read_at(handle,offset,count,budget):
            if cut=='before_first_content_read':trigger()
            return reading(handle,offset,count,budget)
        with mock.patch.object(engine,'open_component',side_effect=open_at), mock.patch.object(engine,'metadata',side_effect=metadata_at), mock.patch.object(engine,'read_data',side_effect=read_at):
            result=r.coordinator.invoke(cap,r.principal,r.decision)
        self.assertEqual(reached,[True],'required native cut not reached')
        return result

    def substitution_races(self,n):
        external=_validate_hostile_fixture()
        cuts=('before_component_open','after_ancestor_pin','after_final_open_before_metadata','before_first_content_read')
        for cut in cuts:
            with self.subTest(kind=n,cut=cut):
                r=_NativeRig(self,'fixtures/selected/file.bin',b'AIO058')
                cap=r.cap(self)
                source={7:r.repo,8:r.repo/'fixtures/selected',9:r.repo/'fixtures/selected/file.bin'}[n]
                moved=source.with_name(source.name+'-moved')
                link=external/('junction' if n in (7,8) else 'file-link')
                changed=[];blocked=[]
                def attack():
                    try:
                        os.rename(source,moved)
                        changed.append(True)
                        if link is not None:os.rename(link,source)
                    except OSError as error:
                        if error.winerror not in (5,32):raise
                        blocked.append(error.winerror)
                try:
                    result=self._at_cut(r,cap,cut,attack)
                    self.assertTrue(changed or blocked,'no mutation attempted')
                    self.assertIn(result.invocation.data,(None,b'AIO058'))
                    if changed:self.assertIsNone(result.invocation.data)
                    self.assertEqual(_count(r),1)
                finally:
                    r.root.close()
                    if changed:
                        if link is not None and os.path.lexists(source):os.rename(source,link)
                        os.rename(moved,source)

    def mutation_races(self):
        probe=_fixture_control()
        cuts=('before_component_open','after_ancestor_pin','after_final_open_before_metadata','before_first_content_read')
        variants=('growth','truncation','same_size_write','hard_link','posix_link','posix_rename')
        for variant in variants:
            for cut in cuts:
                for repetition in range(2):
                    with self.subTest(variant=variant,cut=cut,repetition=repetition):
                        r=_NativeRig(self,'fixtures/selected/file.bin',b'AIO058')
                        cap=r.cap(self);control=probe.Native()
                        final=r.repo/'fixtures/selected/file.bin'
                        outside=r.h.root.parent/'outside-sentinel.bin';outside.write_bytes(b'OUTSIDE-SYNTHETIC')
                        replacement=final.with_name('replacement.bin');replacement.write_bytes(b'REPLACEMENT')
                        outside_handle=control.control_open(outside,access=0,share=3)
                        source_handle=control.control_open(final,access=0,share=7)
                        replacement_handle=control.control_open(replacement,access=probe.DELETE,share=7)
                        outside_id=control.metadata(outside_handle).identity
                        attempted=[];alias=final.with_name('alias.bin')
                        def attack():
                            attempted.append(True)
                            try:
                                if variant in ('growth','truncation','same_size_write'):
                                    with control.control_open(final,access=probe.FILE_WRITE_DATA,share=7) as writer:
                                        if variant=='growth':control.set_end_of_file(writer,65537)
                                        elif variant=='truncation':control.set_end_of_file(writer,3)
                                        else:control.write_at(writer,b'CHANGE',0)
                                elif variant=='hard_link':
                                    control.native_link(source_handle,alias)
                                    try:
                                        with control.control_open(alias,access=probe.DELETE,share=7) as handle:control.native_unlink(handle)
                                    except probe.NativeError as error:
                                        if error.winerror not in (5,32):raise
                                elif variant=='posix_link':control.native_link(outside_handle,final,replace=True,posix=True)
                                else:control.native_rename(replacement_handle,final,replace=True,posix=True)
                            except probe.NativeError as error:
                                if error.winerror not in (5,32):raise
                        try:
                            result=self._at_cut(r,cap,cut,attack)
                            self.assertEqual(attempted,[True])
                            self.assertEqual(control.metadata(outside_handle).identity,outside_id)
                            self.assertEqual(control.metadata(outside_handle).path,'\\\\?\\'+str(outside))
                            allowed=(None,b'AIO058',b'AIO',b'CHANGE',b'REPLACEMENT')
                            self.assertIn(result.invocation.data,allowed)
                            self.assertNotEqual(result.invocation.data,b'OUTSIDE-SYNTHETIC')
                            self.assertEqual(_count(r),1)
                        finally:
                            for handle in tuple(control._handles):handle.close()
                            self.assertEqual(control.handle_count,0)

    def mapping_exclusion(self):
        probe=_fixture_control()
        for kind in ('view','section','reader'):
            r=_NativeRig(self,'fixtures/mapped.bin',b'A'*4096)
            control=probe.Native();control.roots_created.append(str(r.repo.parent))
            target=r.repo/'fixtures/mapped.bin'
            identity=control.identity(target)
            if kind!='reader':
                with probe.WritableState(control,target,identity,kind):
                    result=r.invoke(self)
                    self.assertEqual(result.invocation.reason,'containment_rejected')
                    self.assertIsNone(result.invocation.data)
            else:
                original=r.root._native.read_data;reached=[]
                def challenge(handle,offset,count,budget):
                    if not reached:
                        with self.assertRaises(probe.NativeError) as failure:control.fixture_writer_open(target)
                        self.assertEqual(failure.exception.winerror,32)
                        section=control.kernel.CreateFileMappingW(probe.HANDLE(handle.value),None,4,0,4096,None)
                        if section:
                            control.kernel.CloseHandle(section)
                            self.fail('read-only production target made writable mapping')
                        self.assertEqual(ctypes.get_last_error(),5)
                        reached.append(True)
                    return original(handle,offset,count,budget)
                with mock.patch.object(r.root._native,'read_data',side_effect=challenge):result=r.invoke(self)
                self.assertEqual(result.invocation.data,b'A'*4096);self.assertEqual(reached,[True])
            with control.fixture_writer_open(target):pass
            self.assertEqual(control.handle_count,0);self.assertEqual(control.view_count,0)

    def group_J(self,n):
        if n==7:
            self.assertFalse(bool(ctypes.windll.shell32.IsUserAnAdmin()))
            r=_NativeRig(self)
            cap=r.cap(self)
            observed=[]
            original=r.root._native.open_component
            def confirm(component,parent=None,directory=False):
                self.assertEqual(_count(r),1)
                self.assertEqual(cap._cell.state,'CONSUMED')
                self.assertTrue(r.a.guard.thread.read)
                self.assertTrue(r.a.guard.thread.leaf)
                self.assertTrue(cap._cell.lock.acquire(blocking=False))
                cap._cell.lock.release()
                with closing(_connect(r)) as c:
                    c.execute('BEGIN IMMEDIATE')
                    c.execute('ROLLBACK')  # W was released before target action.
                observed.append(component)
                return original(component,parent,directory)
            with mock.patch.object(r.root._native,'open_component',side_effect=confirm):
                outcome=r.coordinator.invoke(cap,r.principal,r.decision)
            self.assertEqual(outcome.entry_result.outcome,'entered')
            self.assertEqual(outcome.invocation.status,'completed')
            self.assertEqual(outcome.invocation.data,FIRST_BYTES)
            self.assertEqual(outcome.invocation.byte_count,len(FIRST_BYTES))
            self.assertEqual(observed,['fixtures','aio-058-first-read.bin'])
            self.assertEqual(len(r.root._native.handles),len(r.root._state.handles))
            self.assertEqual(_count(r),1)
            self.assertEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'terminal_capability')
            history=r.coordinator.history(cap)
            self.assertEqual(history.outcome,'historical_entry')
            with self.assertRaises(TypeError):native._invoke_repository_file_read(history.entry,r.root,FIRST_RESOURCE)
            r.clock.value+=timedelta(seconds=31)
            facade=claims.adapter._create_owned_dispatch_claim_lease(r.session)
            new_claim=facade.claim(claims.token(2)).claim
            self.assertIsNotNone(new_claim)
            subject=r.a.subject(new_claim,facade._executor,r.run,r.binding_value)
            decision=r.a.mint_entry_decision(subject,r.principal,
                provenance_reference='aio058-no-second-entry',approval_session_id='aio058-no-second-entry',
                valid_from=r.clock.value-timedelta(seconds=1),valid_until=r.clock.value+timedelta(minutes=4))
            with r.a.guard.mutation_scope(r.h.human,'proof_mint'):r.h.human._minted[id(decision)]=decision
            prepared=r.a.prepare(subject,r.principal,decision)
            self.assertEqual(prepared.outcome,'prepared')
            second=r.coordinator.invoke(prepared.capability,r.principal,decision)
            self.assertEqual(second.entry_result.outcome,'already_entered')
            self.assertEqual(_count(r),1)
            print('AIO058_FIRST_EFFECT '+json.dumps(dict(resource=FIRST_RESOURCE,administrator=False,
                synthetic_hex=FIRST_BYTES.hex(),sha256=hashlib.sha256(FIRST_BYTES).hexdigest(),
                entry_count=1,entry_before_effect=True,second_invocation=False,native_cleanup=True)))
        elif n==3:
            self.group_E(1)
            for failure in ('function','signature','root'):
                r=_NativeRig(self);cap=r.cap(self);availability=r.coordinator._availability
                def unavailable(cell):
                    if failure=='function':r.root._native.functions['NtReadFile']=object()
                    elif failure=='signature':r.root._native.functions['NtReadFile'].argtypes=[]
                    else:object.__setattr__(r.root,'_path','wrong-root')
                    return availability(cell)
                with mock.patch.object(r.coordinator,'_availability',side_effect=unavailable):
                    result=r.coordinator.invoke(cap,r.principal,r.decision)
                self.assertEqual(result.entry_result.outcome,'entered')
                self.assertEqual(result.invocation.reason,'adapter_unavailable');self.assertIsNone(result.invocation.data)
                self.assertEqual(_count(r),1)
        elif n==8:
            for status in ('failed_before_content','failed_after_content','ambiguous'):
                with self.assertRaises(ValueError):entry._InvocationOutcome(status,'read_failure',b'synthetic',9)
            self.assertEqual(entry._InvocationOutcome('completed','effect_completed',b'',0).data,b'')
        elif n==6:
            changes=(('identity',(0,b'X'*16)),('file_type',3),('directory',True),
                ('delete_pending',True),('tag',0x42),('nlink',2),('size',99),('write_time',0),('change_time',0))
            for attribute,value in changes:
                r=_NativeRig(self,'fixtures/drift.bin',b'known')
                original=r.root._native.metadata;calls=[]
                def changed(handle,directory=False):
                    result=original(handle,directory)
                    if not directory:
                        calls.append(True)
                        if len(calls)==2:return replace(result,**{attribute:value})
                    return result
                with mock.patch.object(r.root._native,'metadata',side_effect=changed):outcome=r.invoke(self)
                self.assertEqual(outcome.invocation.reason,'resource_changed')
                self.assertIsNone(outcome.invocation.data)
        else:
            self.native_profile(n)

    def group_K(self,n):
        if n in (1,2,3):
            import subprocess,sys
            r=self.rig();cap=r.cap(self)
            cut={1:'entry.before_insert',2:'entry.after_insert',3:'entry.after_commit_before_response'}[n]
            bootstrap="import sys; sys.path.insert(0,sys.argv[1]); from tests.test_durable_execution_entry_and_controlled_invocation import _entry_crash_probe; _entry_crash_probe(*sys.argv[2:])"
            command=[sys.executable,'-I','-B','-c',bootstrap,str(ROOT),str(r.fixture.root),
                str(r.store.configuration.database_path),r.fixture.nonce,cut]
            environment={key:os.environ[key] for key in ('SystemRoot','WINDIR') if key in os.environ}
            environment.update(TEMP=str(TEMP),TMP=str(TEMP))
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                cwd=r.fixture.root,env=environment,shell=False,creationflags=0x08000000)
            try:
                try:output,error=child.communicate(timeout=20)
                except subprocess.TimeoutExpired:
                    child.kill();child.communicate();raise AssertionError('owned storage child timed out') from None
            finally:
                if child.poll() is None:child.kill();child.wait()
            self.assertEqual(child.returncode,93,error.decode('utf-8','replace'))
            self.assertLessEqual(len(output),8192);self.assertEqual(error,b'')
            self.assertTrue(output.startswith(b'AIO058_STORAGE_CRASH '))
            evidence=json.loads(output.split(b' ',1)[1]);self.assertEqual(evidence['cut'],cut)
            self.assertFalse(evidence['administrator']);self.assertEqual(evidence['generation'],2)
            r.fixture._open().verified_settings()
            self.assertEqual(_count(r),int(n==3))
            self.assertIn(_enter(r,cap).outcome,('stale_generation','already_entered'))
            self.assertEqual(_enter(r,cap).outcome,'terminal_capability')
        elif n in (7,8):self.group_E(7)
        else:
            self.native_fault(n)

    def group_F(self,n):
        if n in (1,2):
            r=self.rig();old=r.cap(self)
            capabilities=(old,old) if n==1 else (old,_new_generation(r,self))
            barrier=Barrier(3);results=[]
            def attempt(cap):
                barrier.wait(5)
                results.append(_enter(r,cap))
            workers=[Thread(target=attempt,args=(cap,)) for cap in capabilities]
            for worker in workers:worker.start()
            barrier.wait(5)
            for worker in workers:
                worker.join(5);self.assertFalse(worker.is_alive())
            self.assertEqual(sum(x.outcome=='entered' for x in results),1)
            self.assertEqual(_count(r),1)
            if n==2:self.assertIn(next(x.outcome for x in results if x.outcome!='entered'),('already_entered','stale_generation'))
        elif n in (3,4,5):
            for first in ('entry','mutation'):
                r=self.rig();cap=r.cap(self)
                if first=='entry':self.assertEqual(_enter(r,cap).outcome,'entered')
                if n==3:
                    newer=_new_generation(r,self)
                    if first=='mutation':self.assertEqual(_enter(r,cap).outcome,'stale_generation')
                    else:self.assertEqual(_enter(r,newer).outcome,'already_entered')
                elif n==4:
                    r.clock.value=claims.T+timedelta(seconds=1)
                    self.assertEqual(r.fixture._renew(r.claim).outcome,'newly_renewed')
                    if first=='mutation':self.assertEqual(_enter(r,cap).outcome,'entered')
                else:
                    r.fixture._revoke(r.grant)
                    if first=='mutation':self.assertEqual(_enter(r,cap).outcome,'revoked')
                    else:self.assertEqual(_history(r,cap).outcome,'historical_entry')
            if n==5:self.post_entry_survival(revoke=True)
        elif n in (6,7):
            self.entry_authority_serialization(n)
        elif n==10:
            self.post_entry_survival(revoke=True,expire=True)
        elif n==8:
            self.entry_teardown_serialization()
        else:
            self.entry_reentry_and_root_teardown()

    def entry_teardown_serialization(self):
        import time
        for action in ('close','fence'):
            with self.subTest(action=action):
                r=_NativeRig(self);cap=r.cap(self);held,release,done=Event(),Event(),Event()
                results=[];errors=[]
                availability=r.coordinator._availability
                def pause(cell):
                    held.set()
                    if not release.wait(5):raise AssertionError('Entry teardown barrier timed out')
                    return availability(cell)
                def invoke():
                    try:results.append(r.coordinator.invoke(cap,r.principal,r.decision))
                    except BaseException as error:errors.append(error)
                def teardown():
                    try:getattr(r.session,action)();done.set()
                    except BaseException as error:errors.append(error)
                with mock.patch.object(r.coordinator,'_availability',side_effect=pause):
                    worker=Thread(target=invoke);worker.start();self.assertTrue(held.wait(5))
                    closer=Thread(target=teardown);closer.start()
                    try:
                        deadline=time.monotonic()+5
                        while r.session._state=='live' and time.monotonic()<deadline:time.sleep(.005)
                        self.assertIn(r.session._state,('closing','fencing'))
                        self.assertFalse(done.is_set());self.assertEqual(_count(r),1)
                    finally:release.set();worker.join(5);closer.join(5)
                self.assertFalse(worker.is_alive());self.assertFalse(closer.is_alive());self.assertEqual(errors,[])
                self.assertTrue(done.is_set());self.assertEqual(results[0].entry_result.outcome,'entered')
                self.assertEqual(results[0].invocation.status,'failed_before_content')
                self.assertEqual(results[0].invocation.reason,'ownership_lost')
                self.assertEqual(_count(r),1);self.assertEqual(cap._cell.state,'CONSUMED')
                self.assertNotEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'entered')

    def entry_reentry_and_root_teardown(self):
        import time
        r=_NativeRig(self);cap=r.cap(self)
        def reject_reentry(cell):
            with self.assertRaises(RuntimeError):r.root.close()
            with mock.patch.object(type(r.session),'operation',side_effect=AssertionError('earlier S acquisition')):
                self.assertEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'invalid_integration')
                self.assertEqual(r.coordinator.history(cap).outcome,'invalid_integration')
            with self.assertRaises(jit._JitFailure):
                with r.a.guard.mutation_scope(r.h.human,'withdrawal'):pass
            request=r.coordinator._request(cell)
            operation=entry._EntryOperation(r.a,cell,r.principal,r.decision)
            with r.a.guard.leaf(),mock.patch.object(r.store,'_open_existing',side_effect=AssertionError('earlier W acquisition')) as opening:
                self.assertEqual(r.store._enter_execution(request,operation).outcome,'invalid_integration')
                opening.assert_not_called()
            return False
        with mock.patch.object(r.coordinator,'_availability',side_effect=reject_reentry):result=r.coordinator.invoke(cap,r.principal,r.decision)
        self.assertEqual(result.invocation.reason,'adapter_unavailable');self.assertEqual(_count(r),1)
        r=_NativeRig(self);cap=r.cap(self);held,release,done=Event(),Event(),Event();results=[];errors=[]
        availability=r.coordinator._availability
        def pause(cell):
            held.set()
            if not release.wait(5):raise AssertionError('root teardown barrier timed out')
            return availability(cell)
        def invoke():
            try:results.append(r.coordinator.invoke(cap,r.principal,r.decision))
            except BaseException as error:errors.append(error)
        def close():
            try:r.root.close();done.set()
            except BaseException as error:errors.append(error)
        with mock.patch.object(r.coordinator,'_availability',side_effect=pause):
            worker=Thread(target=invoke);worker.start();self.assertTrue(held.wait(5))
            closer=Thread(target=close);closer.start()
            try:
                deadline=time.monotonic()+5
                while not r.root._state.closing and time.monotonic()<deadline:time.sleep(.005)
                self.assertTrue(r.root._state.closing);self.assertFalse(done.is_set())
            finally:release.set();worker.join(5);closer.join(5)
        self.assertEqual(errors,[]);self.assertFalse(worker.is_alive());self.assertFalse(closer.is_alive())
        self.assertTrue(done.is_set());self.assertEqual(results[0].invocation.reason,'adapter_unavailable')
        self.assertEqual(_count(r),1);self.assertEqual(r.root._native.handles,set())

    def entry_authority_serialization(self,n):
        kinds=('issuer_disabled','issuer_reenabled') if n==6 else ('logout','withdrawal','policy_deny')
        for kind in kinds:
            issuer_kind='policy' if kind=='policy_deny' else 'human'
            for order in ('mutation_first','entry_first'):
                with self.subTest(kind=kind,order=order):
                    r=self.rig(issuer_kind=issuer_kind);cap=r.cap(self)
                    def mutate():
                        if kind.startswith('issuer'):
                            r.issuer.disable()
                            if kind=='issuer_reenabled':r.issuer.enable()
                        elif kind=='logout':r.identity.change('logout',valid=False)
                        elif kind=='withdrawal':r.human.change('withdrawal',valid=False)
                        else:r.policy.change('policy_revision',valid=False)
                    if order=='mutation_first':
                        mutate();self.assertNotEqual(_enter(r,cap).outcome,'entered');self.assertEqual(_count(r),0)
                    else:
                        held,release,changed=Event(),Event(),Event();results=[];errors=[]
                        def pause(point):
                            if point=='entry.before_commit':
                                held.set()
                                if not release.wait(5):raise AssertionError('Entry barrier timed out')
                        def enter():
                            try:results.append(_enter(r,cap))
                            except BaseException as error:errors.append(error)
                        def mutation():
                            try:mutate();changed.set()
                            except BaseException as error:errors.append(error)
                        with mock.patch.object(r.store,'_fault',side_effect=pause):
                            reader=Thread(target=enter);reader.start();self.assertTrue(held.wait(5))
                            writer=Thread(target=mutation);writer.start()
                            try:self.assertFalse(changed.wait(.05),'G/P did not serialize mutation')
                            finally:release.set();reader.join(5);writer.join(5)
                        self.assertFalse(reader.is_alive());self.assertFalse(writer.is_alive());self.assertEqual(errors,[])
                        self.assertEqual(results[0].outcome,'entered');self.assertEqual(_count(r),1)
                        self.assertTrue(changed.is_set());self.assertEqual(cap._cell.state,'CONSUMED')
                        self.assertEqual(_history(r,cap).outcome,'historical_entry')

    def post_entry_survival(self,*,revoke=False,expire=False,before_commit_expire=False):
        r=_NativeRig(self);cap=r.cap(self);accepted=[]
        def check(cell):
            self.assertEqual(_count(r),1)
            if expire:r.clock.value+=timedelta(minutes=6)
            if revoke:
                result=r.store.revoke_or_return_existing(claims._mint_revocation_request(r.store.configuration.authorization_domain_id,r.grant))
                self.assertIn(result.outcome.value,('newly_revoked','exact_retry'))
            with r.a.guard.leaf():
                r.coordinator._begin_native(r.coordinator._original,r.root,FIRST_RESOURCE)
            accepted.append(True)
            return False  # Prove original remains valid; no native target action.
        def before_commit(point):
            if before_commit_expire and point=='entry.before_commit':r.clock.value+=timedelta(minutes=6)
        with mock.patch.object(r.coordinator,'_availability',side_effect=check),mock.patch.object(r.store,'_fault',side_effect=before_commit):
            result=r.coordinator.invoke(cap,r.principal,r.decision)
        self.assertEqual(result.entry_result.outcome,'entered');self.assertEqual(accepted,[True])
        self.assertEqual(_count(r),1);self.assertEqual(result.invocation.reason,'adapter_unavailable')
        self.assertEqual(r.coordinator.history(cap).outcome,'historical_entry')
        self.assertEqual(r.coordinator.invoke(cap,r.principal,r.decision).entry_result.outcome,'terminal_capability')

    def corrupt_snapshot(self,r,mutation,*,restore=True):
        with closing(_connect(r)) as c:
            c.execute('PRAGMA foreign_keys=OFF')
            c.execute('PRAGMA ignore_check_constraints=ON')
            triggers=c.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger'").fetchall()
            for row in triggers:c.execute('DROP TRIGGER '+row['name'])
            mutation(c)
            if restore:
                for row in triggers:c.execute(row['sql'])
        self.assertNotEqual(_history(r,r._audit_cap).outcome,'historical_entry')
        with self.assertRaises(store_module.SqliteAdmissionStoreError):r.fixture._open()

    def group_G(self,n):
        if n==15:
            for equal in (False,True):
                r=self.rig();cap,e=self.asserted_entry(r)
                if not equal:
                    r.clock.value=claims.T+timedelta(seconds=5)
                    self.assertEqual(r.fixture._renew(r.claim).outcome,'newly_renewed')
                    r.clock.value=claims.T+timedelta(seconds=36);_new_generation(r,self)
                r.fixture._revoke(r.grant)
                self.assertEqual(_history(r,cap).outcome,'historical_entry')
            return
        branches={9:('malformed','noncanonical','key_disagreement','negative_key'),
            10:('trigger','index','foreign_key'),11:('checksum','prefix','metadata'),
            12:('renewal_gap','overlap','entry_before_acquisition','entry_at_expiry'),
            14:('regressed_watermark','missing_watermark'),16:('unrelated_candidate','unrelated_entry')}.get(n,('single',))
        for branch in branches:
            with self.subTest(branch=branch):
                r=self.rig();cap,e=self.asserted_entry(r);r._audit_cap=cap
                if n==12:
                    r.clock.value=claims.T+timedelta(seconds=5)
                    self.assertEqual(r.fixture._renew(r.claim).outcome,'newly_renewed')
                    if branch=='overlap':r.clock.value=claims.T+timedelta(seconds=35);_new_generation(r,self)
                if n==16 and branch=='unrelated_candidate':foreign=r.fixture._admit(99,r.store)
                def mutation(c):
                    if n in (1,2):c.execute('DELETE FROM '+('agent_execution_dispatch_intents' if n==1 else 'agent_execution_dispatch_admissions'))
                    elif n in (3,4,5,6):
                        field={3:'claim_id',4:'lease_generation',5:'executor_instance_id',6:'grant_id'}[n]
                        value=99 if n==4 else 'foreign' if n==6 else claims.token(999)
                        c.execute('UPDATE agent_execution_entries SET '+field+'=?',(value,))
                    elif n in (7,8,13):
                        row=list(c.execute('SELECT * FROM agent_execution_entries').fetchone())
                        if n==8:row[4]=claims.token(999)
                        if n==13:row[6]+=1
                        with self.assertRaises(sqlite3.IntegrityError):c.execute('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row)
                        # Even a corruption mechanism that removes the D key is
                        # rejected by the whole schema audit, never winner selection.
                        c.execute('CREATE TABLE entry_corruption_copy AS SELECT * FROM agent_execution_entries')
                        c.execute('DROP TABLE agent_execution_entries')
                        c.execute('ALTER TABLE entry_corruption_copy RENAME TO agent_execution_entries')
                        c.execute('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row)
                    elif n==9:
                        if branch=='malformed':c.execute('UPDATE agent_execution_entries SET entry_time=?',('x'*27,))
                        elif branch=='noncanonical':c.execute('UPDATE agent_execution_entries SET entry_time=?',(e.entry_time[:-1]+'z',))
                        else:c.execute('UPDATE agent_execution_entries SET entry_time_key=?',(-1 if branch=='negative_key' else e.entry_time_key+1,))
                    elif n==10:
                        if branch=='trigger':return
                        if branch=='index':c.execute('CREATE INDEX aio058_corrupt_index ON agent_execution_entries(entry_time_key)')
                        else:
                            row=tuple(c.execute('SELECT * FROM agent_execution_entries').fetchone())
                            sql=c.execute("SELECT sql FROM sqlite_schema WHERE name='agent_execution_entries'").fetchone()[0]
                            sql=sql[:sql.index('    FOREIGN KEY')].rstrip(' ,\n\r')+'\n) STRICT, WITHOUT ROWID'
                            c.execute('DROP TABLE agent_execution_entries');c.execute(sql)
                            c.execute('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row)
                    elif n==11:
                        if branch=='checksum':c.execute('UPDATE admission_schema_migrations SET sha256=? WHERE migration_id=4',('0'*64,))
                        elif branch=='prefix':c.execute('DELETE FROM admission_schema_migrations WHERE migration_id=3')
                        else:c.execute("UPDATE admission_ledger_metadata SET schema_manifest_id='foreign'")
                    elif n==12:
                        if branch=='renewal_gap':c.execute('UPDATE agent_execution_dispatch_renewals SET renewal_sequence=2')
                        elif branch=='overlap':
                            _,text,key=store_module._canonical_decision_time(claims.T+timedelta(seconds=34))
                            _,until,ukey=store_module._canonical_decision_time(claims.T+timedelta(seconds=64))
                            c.execute('UPDATE agent_execution_dispatch_claims SET acquired_at=?,acquired_at_key=?,lease_until=?,lease_until_key=? WHERE lease_generation=2',(text,key,until,ukey))
                        else:
                            instant=claims.T-timedelta(microseconds=1) if branch=='entry_before_acquisition' else claims.T+timedelta(seconds=35)
                            _,text,key=store_module._canonical_decision_time(instant)
                            c.execute('UPDATE agent_execution_entries SET entry_time=?,entry_time_key=?',(text,key))
                            if branch=='entry_at_expiry':c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?',(text,key))
                    elif n==14:
                        if branch=='missing_watermark':c.execute('UPDATE admission_ledger_metadata SET last_decision_time=NULL,last_decision_time_key=NULL')
                        else:
                            _,text,key=store_module._canonical_decision_time(claims.T-timedelta(microseconds=1))
                            c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?',(text,key))
                    elif branch=='unrelated_candidate':
                        c.execute("UPDATE agent_execution_dispatch_admissions SET grant_json='{}' WHERE grant_id=?",(foreign.grant_id,))
                    else:
                        row=list(c.execute('SELECT * FROM agent_execution_entries').fetchone());row[3]='unrelated-dispatch'
                        c.execute('INSERT INTO agent_execution_entries VALUES (?,?,?,?,?,?,?,?,?)',row)
                self.corrupt_snapshot(r,mutation,restore=n!=10 or branch!='trigger')

    def _old_source(self,f,version,name):
        config=claims.fixture.config_for(f.root/(name+'.sqlite3'))
        claims._old_ledger(config,2 if version==3 else version,nonempty=True)
        if version==3:
            with closing(claims.outbox._connect(config.database_path)) as c:
                c.execute("UPDATE admission_ledger_metadata SET migration_state='dirty'")
                migration=store_module._migration_bytes()[2]
                for statement in store_module._sql_statements(migration[3]):c.execute(statement)
                c.execute('INSERT INTO admission_schema_migrations VALUES (?,?,?)',migration[:3])
                c.execute('PRAGMA user_version=3')
                c.execute('UPDATE admission_ledger_metadata SET schema_version=3,schema_manifest_id=?',(store_module._schema_manifest_id(3),))
                c.execute("UPDATE admission_ledger_metadata SET migration_state='clean'")
                identity=tuple(c.execute('SELECT * FROM agent_execution_dispatch_intents ORDER BY 1,2,3,4 LIMIT 1').fetchone())
                _,text,key=store_module._canonical_decision_time(claims.T)
                _,until,until_key=store_module._canonical_decision_time(claims.T+timedelta(seconds=30))
                c.execute('INSERT INTO agent_execution_dispatch_claims VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (claims.token(101),*identity,claims.token(102),1,text,key,until,until_key))
                _,renewed,rkey=store_module._canonical_decision_time(claims.T+timedelta(seconds=5))
                _,expiry,ekey=store_module._canonical_decision_time(claims.T+timedelta(seconds=35))
                c.execute('INSERT INTO agent_execution_dispatch_renewals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (claims.token(103),claims.token(101),*identity,claims.token(102),1,1,renewed,rkey,expiry,ekey))
                c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?',(renewed,rkey))
        return config

    def group_H(self,n):
        f=claims.DispatchClaimLeaseTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        if n in (2,3,4,9,10,11,12):
            version={2:3,3:2,4:1}.get(n,3)
            cuts=('migration.before_transaction','migration.after_dirty','migration4.after_schema',
                'migration.after_history_before_version','migration.after_version_publication',
                'migration.after_clean_transition','migration.before_commit') if n==9 else ('none',)
            for index,cut in enumerate(cuts):
                config=self._old_source(f,version,'old-'+str(index))
                with closing(claims.outbox._connect(config.database_path)) as c:
                    source_schema={row['name']:row['sql'] for row in c.execute("SELECT name,sql FROM sqlite_schema WHERE substr(name,1,7)<>'sqlite_'")}
                before=claims._snapshot(config.database_path)
                with closing(claims.outbox._connect(config.database_path)) as c:
                    history={table:tuple(tuple(row) for row in c.execute('SELECT * FROM '+table+' ORDER BY 1,2,3,4'))
                        for table in ('agent_execution_dispatch_admissions','agent_execution_grant_revocations',
                            'agent_execution_dispatch_intents','legacy_admission_markers','agent_execution_dispatch_claims','agent_execution_dispatch_renewals')
                        if c.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?",(table,)).fetchone()}
                if n==9:
                    def fail(point):
                        if point==cut:raise OSError('synthetic migration crash boundary')
                    with mock.patch.object(store_module.SqliteAgentExecutionDispatchAdmissionStore,'_administration_fault',side_effect=fail):result=f._migrate(config)
                    self.assertNotEqual(result.outcome.value,'migrated')
                    self.assertEqual(claims._snapshot(config.database_path),before)
                    with closing(claims.outbox._connect(config.database_path)) as c:
                        self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],version)
                        self.assertEqual(store_module._schema_fingerprint(c),store_module._EXPECTED_SCHEMA_FINGERPRINTS[version])
                    continue
                if n==10:
                    def unknown(point):
                        if point=='migration.after_commit_before_response':raise OSError('synthetic lost committed response')
                    with mock.patch.object(store_module.SqliteAgentExecutionDispatchAdmissionStore,'_administration_fault',side_effect=unknown):
                        self.assertEqual(f._migrate(config).outcome.value,'commit_unknown')
                elif n==11:
                    with mock.patch.object(store_module,'_commit',side_effect=store_module._CommitUnknown('synthetic uncommitted ambiguity')):
                        self.assertEqual(f._migrate(config).outcome.value,'commit_unknown')
                    self.assertEqual(claims._snapshot(config.database_path),before)
                    self.assertEqual(f._migrate(config).outcome.value,'migrated')
                else:self.assertEqual(f._migrate(config).outcome.value,'migrated')
                with closing(claims.outbox._connect(config.database_path)) as c:
                    self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],4)
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM agent_execution_entries').fetchone()[0],0)
                    self.assertEqual(store_module._schema_fingerprint(c),store_module._EXPECTED_SCHEMA_FINGERPRINTS[4])
                    if version==3:
                        self.assertEqual(c.execute('SELECT COUNT(*) FROM agent_execution_dispatch_claims').fetchone()[0],1)
                        self.assertEqual(c.execute('SELECT COUNT(*) FROM agent_execution_dispatch_renewals').fetchone()[0],1)
                    for table,rows in history.items():self.assertEqual(tuple(tuple(row) for row in c.execute('SELECT * FROM '+table+' ORDER BY 1,2,3,4')),rows)
                    destination={row['name']:row['sql'] for row in c.execute("SELECT name,sql FROM sqlite_schema WHERE substr(name,1,7)<>'sqlite_'")}
                guards={'agent_execution_dispatch_'+table+'_operational_insert' for table in ('intents','claims','renewals')}
                for name,sql in source_schema.items():
                    if name not in guards:self.assertEqual(destination[name],sql)
                f._open(config)
                self.assertEqual(f._migrate(config).outcome.value,'already_current')
            if n==11:
                config=self._old_source(f,3,'mixed-source')
                with closing(claims.outbox._connect(config.database_path)) as c:
                    c.execute("UPDATE admission_ledger_metadata SET migration_state='dirty'")
                    c.execute('UPDATE admission_ledger_metadata SET schema_version=4,schema_manifest_id=?',(store_module._schema_manifest_id(4),))
                    c.execute("UPDATE admission_ledger_metadata SET migration_state='clean'")
                mixed=claims._snapshot(config.database_path)
                self.assertNotIn(f._migrate(config).outcome.value,('migrated','already_current'))
                self.assertEqual(claims._snapshot(config.database_path),mixed)
        elif n==5:
            for version in (1,2,3):
                config=self._old_source(f,version,'reject-old-'+str(version))
                with self.assertRaises(store_module.SqliteAdmissionStoreError):f._open(config)
            for variant in ('newer','unknown','dirty'):
                config=claims.fixture.config_for(f.root/(variant+'.sqlite3'))
                self.assertEqual(store_module.SqliteAgentExecutionDispatchAdmissionStore.provision(config,access=claims.fixture.administration_access(config)).outcome.value,'provisioned')
                with closing(claims.outbox._connect(config.database_path)) as c:
                    if variant=='dirty':c.execute("UPDATE admission_ledger_metadata SET migration_state='dirty'")
                    else:c.execute('PRAGMA user_version='+('5' if variant=='newer' else '0'))
                with self.assertRaises(store_module.SqliteAdmissionStoreError):f._open(config)
        elif n==6:
            r=self.rig();cap,e=self.asserted_entry(r)
            self.assertEqual(r.fixture._migrate().outcome.value,'already_current')
            r._audit_cap=cap
            self.corrupt_snapshot(r,lambda c:c.execute('UPDATE agent_execution_entries SET entry_time_key=entry_time_key+1'))
            self.assertNotEqual(r.fixture._migrate().outcome.value,'already_current')
            self.assertEqual(_count(r),1)
        elif n==7:
            expected=('6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed',
                'eee70c9d3e31dca036e716fc8b0ad42c78c97bb07cc5c6e323eaa7290e0ba6db',
                'c9163740873586ab39ee760c292cdcdd07bf050ee06f37c29614c5e3a8144949')
            self.assertEqual(tuple(value[2] for value in store_module._migration_bytes()[:3]),expected)
        elif n==8:
            for variant in ('checksum','missing','reordered'):
                config=claims.fixture.config_for(f.root/(variant+'.sqlite3'))
                store_module.SqliteAgentExecutionDispatchAdmissionStore.provision(config,access=claims.fixture.administration_access(config))
                with closing(claims.outbox._connect(config.database_path)) as c:
                    triggers=c.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' AND tbl_name='admission_schema_migrations'").fetchall()
                    for trigger in triggers:c.execute('DROP TRIGGER '+trigger['name'])
                    if variant=='checksum':c.execute("UPDATE admission_schema_migrations SET sha256=? WHERE migration_id=4",('0'*64,))
                    elif variant=='missing':c.execute('DELETE FROM admission_schema_migrations WHERE migration_id=4')
                    else:c.execute('UPDATE admission_schema_migrations SET migration_id=5 WHERE migration_id=4')
                    for trigger in triggers:c.execute(trigger['sql'])
                with self.assertRaises(store_module.SqliteAdmissionStoreError):f._open(config)
        else:
            f._setup(count=0)
            self.assertEqual(f._migrate(f.configuration).outcome.value,'already_current')
            with closing(claims.outbox._connect(f.configuration.database_path)) as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM agent_execution_entries').fetchone()[0],0)

    def group_M(self,n):
        paths=('engineering_orchestration/_execution_entry_and_controlled_invocation.py',
            'engineering_orchestration/_native_repository_file_read.py')
        for path in paths:
            source=(ROOT/path).read_text(encoding='utf-8');tree=ast.parse(source)
            forbidden={'subprocess','socket','urllib','http','requests','importlib','experiments'}
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertFalse(any(alias.name.split('.')[0] in forbidden for alias in node.names))
                if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').split('.')[0] in forbidden)
            self.assertNotIn('FILE_SHARE_WRITE',source)
            self.assertNotIn('os.system(',source)
        self.assertEqual(len(SCENARIO_IDS),128)
        self.assertEqual(len(E_TRACE),24)
        self.assertEqual(entry.__all__,())
        self.assertEqual(native.__all__,())

    def _regression(self,case):
        result=unittest.TestResult();case.run(result)
        self.assertEqual(result.errors,[])
        self.assertEqual(result.failures,[])
        self.assertEqual(result.skipped,[])

    def group_L(self,n):
        self.group_M(n)
        if n==1:
            from tests.test_windows_local_authorization_domain_owner import WindowsLocalAuthorizationDomainOwnerWin32Tests as Case
            for name in ('test_session_is_adapter_created_noncopyable_and_closed_fail_closed',
                    'test_held_ledger_pin_denies_rename_and_replacement',
                    'test_close_waits_for_active_operation_and_rejects_new_work'):
                self._regression(Case(name))
        elif n==2:
            from tests.test_agent_execution_authorization_grant_producer import ProducerContractTests,ProducerFailureTests
            self._regression(ProducerContractTests('test_locked_api_and_capabilities_are_guarded'))
            self._regression(ProducerFailureTests('test_principal_identity_entitlement_and_authority_failures'))
        elif n==3:
            from tests.test_agent_operation_tool_resolver import TrustedAgentOperationToolBindingResolverTests as Case
            for name in ('test_exact_run_resource_and_all_contract_scope_are_preserved',
                    'test_retired_registration_remains_total_for_historical_resolution',
                    'test_missing_history_and_alias_cannot_remap_or_fallback'):
                self._regression(Case(name))
        elif n==4:
            for name in ('test_C021_canonical_first_claim','test_C027_claim_retry_history',
                    'test_C032_exact_expiry','test_C033_contiguous_restart','test_C037_consumed_grant_expiry',
                    'test_C039_renewal','test_C108_current_vs_history'):
                self._regression(claims.DispatchClaimLeaseTests(name))
        elif n==5:
            for number in (1,4,13,14,57,58,72):self._regression(predecessor.FoundationTests('test_F'+str(number).zfill(2)))
        elif n in (6,8):self.group_H(4)

    # Native/continuation scenarios are added below with exact real fixture
    # contracts; no runtime skip or fabricated scenario PASS is used.


def _scenario(name):
    def test(self):self.run_scenario(name)
    test.__name__='test_'+name
    return test

for _id in SCENARIO_IDS:
    setattr(ProductionScenarios,'test_'+_id,_scenario(_id))


def storage_suite():
    """Explicit interim subset, no discovery and no native target invocation."""
    names=tuple(name for name in SCENARIO_IDS if name[0] in 'ABCDFGHLM')
    return unittest.TestSuite(ProductionScenarios('test_'+name) for name in names)
