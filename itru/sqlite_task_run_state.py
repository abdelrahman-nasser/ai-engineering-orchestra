"""Dedicated bounded local lifecycle Store; never dispatches or restores authority."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
import stat
from threading import RLock

from itru import task_run_state as domain

APPLICATION_ID = 0x49545331
_DDL = (
    ('metadata', 'table', 'CREATE TABLE metadata (singleton INTEGER PRIMARY KEY CHECK(singleton=1), store_id TEXT NOT NULL, project_id TEXT NOT NULL, ddl_hash TEXT NOT NULL) STRICT'),
    ('events', 'table', 'CREATE TABLE events (sequence INTEGER PRIMARY KEY, payload TEXT NOT NULL) STRICT'),
    ('metadata_no_update', 'trigger', "CREATE TRIGGER metadata_no_update BEFORE UPDATE ON metadata BEGIN SELECT RAISE(ABORT, 'immutable metadata'); END"),
    ('metadata_no_delete', 'trigger', "CREATE TRIGGER metadata_no_delete BEFORE DELETE ON metadata BEGIN SELECT RAISE(ABORT, 'immutable metadata'); END"),
    ('events_no_update', 'trigger', "CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable event'); END"),
    ('events_no_delete', 'trigger', "CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'immutable event'); END"),
)
_DDL_HASH = hashlib.sha256(domain.encode([list(item) for item in _DDL]).encode()).hexdigest()


class StateStoreBusyError(RuntimeError):
    pass


class StateCommitUnknownError(RuntimeError):
    """Read current state; never repeat an operation as an execution instruction."""


def _plain(path, *, directory):
    item = path.lstat()
    if (stat.S_IFMT(item.st_mode) != (stat.S_IFDIR if directory else stat.S_IFREG)
            or getattr(item, 'st_file_attributes', 0) & (0x400 | 0x1000 | 0x40000 | 0x400000)
            or path.is_symlink() or (not directory and item.st_nlink != 1)):
        raise OSError('unsupported lifecycle Store object')
    return item.st_dev, item.st_ino


def _security(path, *, directory, establish=False):
    if os.name == 'nt':
        from itru.windows_local_authorization_domain_owner import (
            _apply_security_profile, _validate_security_profile, _current_user_sid,
        )
        sid = _current_user_sid()
        if establish:
            _apply_security_profile(path, sid, directory=directory)
        _validate_security_profile(path, sid, directory=directory,
                                   allow_safe_inheritance=not directory)
    elif os.name == 'posix':
        if establish:
            os.chmod(path, 0o700 if directory else 0o600)
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600):
            raise OSError('lifecycle Store security profile rejected')
    else:
        raise OSError('unsupported lifecycle Store platform')


def _local_path(directory):
    if not isinstance(directory, Path) or not directory.is_absolute():
        raise domain.StateIntegrityError('absolute dedicated directory required')
    if (directory.resolve(strict=False) != directory or '..' in directory.parts
            or str(directory).startswith('\\')):
        raise domain.StateIntegrityError('exact local path required')
    for parent in directory.parents:
        _plain(parent, directory=True)
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise OSError('SQLite 3.37 or newer required')
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetDriveTypeW.argtypes, kernel.GetDriveTypeW.restype = [ctypes.c_wchar_p], ctypes.c_uint
        if kernel.GetDriveTypeW(directory.anchor) != 3:
            raise OSError('fixed local volume required')
    elif os.name != 'posix':
        raise OSError('unsupported local Store platform')


def _lock(file, acquire):
    file.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK if acquire else msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(file.fileno(), (fcntl.LOCK_EX | fcntl.LOCK_NB) if acquire else fcntl.LOCK_UN)


def _connect(path, *, create=False):
    connection = sqlite3.connect(path.as_uri() + ('?mode=rwc' if create else '?mode=rw'),
        uri=True, timeout=5, isolation_level=None, check_same_thread=False)
    try:
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA trusted_schema=OFF')
        if create:
            connection.execute('PRAGMA journal_mode=DELETE')
        if (connection.execute('PRAGMA journal_mode').fetchone() != ('delete',)
                or connection.execute('PRAGMA synchronous').fetchone() != (2,)
                or connection.execute('PRAGMA foreign_keys').fetchone() != (1,)):
            raise domain.StateIntegrityError('unsupported SQLite durability configuration')
        return connection
    except BaseException:
        connection.close()
        raise


class SqliteTaskRunStateStore:
    """One process-owned session; immutable read models confer no execution authority.

    continuation_authorizer is a trusted composition port, not caller evidence.
    It must freshly authenticate Human/policy entitlement for the exact request,
    perform no execution, and return an exact ContinuationApproval or None.
    """
    def __init__(self, directory, *, store_id, project_id, continuation_authorizer=None):
        _local_path(directory)
        domain._text(store_id); domain._text(project_id)
        if continuation_authorizer is not None and not callable(continuation_authorizer):
            raise TypeError('trusted continuation authorizer must be callable')
        self.directory, self.store_id, self.project_id = directory, store_id, project_id
        self._authorizer = continuation_authorizer
        self._pid, self._session_nonce = os.getpid(), secrets.token_hex(32)
        self._mutex, self._active, self._closed = RLock(), False, False
        self._connection = self._lock_file = None
        self._paths = (directory, directory / 'owner.lock', directory / 'state.sqlite3')
        self._identities = tuple(_plain(path, directory=(index == 0))
                                 for index, path in enumerate(self._paths))
        for index, path in enumerate(self._paths):
            _security(path, directory=(index == 0))
        try:
            self._lock_file = (directory / 'owner.lock').open('r+b', buffering=0)
            try:
                _lock(self._lock_file, True)
            except OSError:
                raise StateStoreBusyError('Store already owned') from None
            self._check_session()
            self._connection = _connect(directory / 'state.sqlite3')
            with self._transaction() as (events, tasks):
                for task in tuple(tasks.values()):
                    if any(run.state in domain.UNFINISHED for run in task.runs):
                        self._append(events, tasks, task.task_id, task.revision, 'recover', {})
        except BaseException:
            self.close()
            raise

    @classmethod
    def provision(cls, directory, *, store_id, project_id, continuation_authorizer=None):
        """Explicit administration: only a brand-new dedicated directory, no upgrade."""
        _local_path(directory)
        domain._text(store_id); domain._text(project_id)
        domain.encode(dict(store_id=store_id, project_id=project_id))
        directory.mkdir(mode=0o700)  # Existing paths, including partial stores, fail.
        _security(directory, directory=True, establish=True)
        with (directory / 'owner.lock').open('xb') as file:
            file.write(b'1'); file.flush(); os.fsync(file.fileno())
        _security(directory / 'owner.lock', directory=False, establish=True)
        connection = _connect(directory / 'state.sqlite3', create=True)
        try:
            connection.execute('BEGIN IMMEDIATE')
            for _, _, sql in _DDL:
                connection.execute(sql)
            connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.execute('PRAGMA user_version=1')
            connection.execute('INSERT INTO metadata VALUES (1, ?, ?, ?)', (store_id, project_id, _DDL_HASH))
            connection.execute('COMMIT')
        finally:
            connection.close()
        _security(directory / 'state.sqlite3', directory=False, establish=True)
        return cls(directory, store_id=store_id, project_id=project_id,
                   continuation_authorizer=continuation_authorizer)

    def _check_session(self):
        if self._closed or self._pid != os.getpid():
            raise domain.StateConflictError('closed or foreign process Store session')
        for index, path in enumerate(self._paths):
            if _plain(path, directory=(index == 0)) != self._identities[index]:
                raise domain.StateIntegrityError('Store file identity changed')
            _security(path, directory=(index == 0))
        info = os.fstat(self._lock_file.fileno())
        if ((info.st_dev, info.st_ino) != self._identities[1]
                or self._lock_file.seek(0) != 0 or self._lock_file.read(2) != b'1'):
            raise domain.StateIntegrityError('Store ownership file changed')
        sidecar = self.directory / 'state.sqlite3-journal'
        if sidecar.exists() or sidecar.is_symlink():
            _plain(sidecar, directory=False); _security(sidecar, directory=False)

    def _verify(self):
        connection = self._connection
        if (connection.execute('PRAGMA application_id').fetchone() != (APPLICATION_ID,)
                or connection.execute('PRAGMA user_version').fetchone() != (1,)
                or connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]):
            raise domain.StateIntegrityError('incompatible or corrupt Store')
        actual = tuple(sorted(connection.execute(
            "SELECT name,type,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'").fetchall()))
        if actual != tuple(sorted(_DDL)):
            raise domain.StateIntegrityError('Store schema changed')
        if connection.execute('SELECT * FROM metadata').fetchall() != [(1, self.store_id, self.project_id, _DDL_HASH)]:
            raise domain.StateIntegrityError('Store metadata identity changed')
        rows = connection.execute('SELECT sequence,payload FROM events ORDER BY sequence LIMIT ?',
                                  (domain.MAX_EVENTS + 1,)).fetchall()
        events = []
        for sequence, payload in rows:
            event = domain.decode(payload)
            domain.validate_event(event)
            if type(sequence) is not int or event['sequence'] != sequence:
                raise domain.StateIntegrityError('event index mismatch')
            events.append(event)
        return events, domain.reconstruct(events)

    @contextmanager
    def _transaction(self):
        with self._mutex:
            if self._active:
                raise domain.StateConflictError('recursive Store operation')
            self._check_session()
            self._active = True
            try:
                self._connection.execute('BEGIN IMMEDIATE')
                events, tasks = self._verify()
                yield events, tasks
                self._check_session()
                try:
                    self._connection.execute('COMMIT')
                    self._fault('after_commit')
                except Exception:
                    raise StateCommitUnknownError('commit outcome unknown; query state') from None
            except sqlite3.Error:
                raise domain.StateIntegrityError('Store SQL integrity/storage failure') from None
            finally:
                if self._connection.in_transaction:
                    self._connection.execute('ROLLBACK')
                self._active = False

    def _fault(self, point):
        """Private test seam; production has no fault behavior."""

    def _append(self, events, tasks, task_id, expected_revision, operation, data):
        if type(expected_revision) is not int or expected_revision < 0:
            raise domain.StateIntegrityError('invalid expected revision')
        task = tasks.get(task_id)
        if (0 if task is None else task.revision) != expected_revision:
            raise domain.StateConflictError('stale Task revision')
        if len(events) >= domain.MAX_EVENTS:
            raise domain.StateIntegrityError('Store history limit')
        event = dict(format_version=1, sequence=len(events)+1, task_id=task_id,
                     revision=expected_revision+1, operation=operation, data=data)
        domain.apply_event(tasks, event)
        self._fault('before_insert')
        self._connection.execute('INSERT INTO events VALUES (?, ?)',
                                 (event['sequence'], domain.encode(event)))
        events.append(event)
        self._fault('after_insert')
        return tasks[task_id]

    def enroll(self, task_id, *, definition_reference):
        domain._text(task_id); domain._text(definition_reference)
        with self._transaction() as (events, tasks):
            if task_id in tasks:
                if tasks[task_id].definition_reference != definition_reference:
                    raise domain.StateConflictError('Task ID already bound')
                return tasks[task_id]
            return self._append(events, tasks, task_id, 0, 'enroll',
                                dict(definition_reference=definition_reference))

    def register_run(self, binding, ledger_identity, *, expected_revision):
        subject = domain.subject_document(binding, ledger_identity)
        task_id = binding.run.contract.task_id
        with self._transaction() as (events, tasks):
            task = tasks.get(task_id)
            if task and task.runs and task.runs[0].binding == binding and task.runs[0].ledger_identity == ledger_identity:
                return task  # Historical exact retry only; never starts a Run.
            return self._append(events, tasks, task_id, expected_revision, 'register', dict(subject=subject))

    def transition(self, task_id, *, expected_revision, operation, reference):
        if operation not in ('block', 'cancel', 'complete', 'stop'):
            raise domain.StateIntegrityError('unsupported explicit Task transition')
        with self._transaction() as (events, tasks):
            return self._append(events, tasks, task_id, expected_revision, operation, dict(reference=reference))

    def start_run(self, task_id, run_id, *, expected_revision):
        with self._transaction() as (events, tasks):
            return self._append(events, tasks, task_id, expected_revision, 'start', dict(run_id=run_id))

    def record_result(self, result, *, expected_revision):
        from itru.agent_execution_result import _is_authoritative_result
        if not _is_authoritative_result(result):
            raise domain.StateIntegrityError('original authoritative Result required')
        binding, ledger = result.tool_binding, result.ledger_identity
        task_id, run_id = binding.run.contract.task_id, binding.run.run_id
        with self._transaction() as (events, tasks):
            task = tasks.get(task_id)
            run = next((item for item in task.runs if item.run_id == run_id), None) if task else None
            if run is None or run.binding != binding or run.ledger_identity != ledger:
                raise domain.StateConflictError('Result/Run subject mismatch')
            if run.result_identity == result.identity and run.state == result.outcome:
                return task  # Passive exact original observation retry, not invocation.
            return self._append(events, tasks, task_id, expected_revision, 'result',
                dict(run_id=run_id, outcome=result.outcome, result_identity=list(result.identity)))

    def continue_task(self, checkpoint, binding, ledger_identity, *, reason):
        if type(checkpoint) is not domain.Checkpoint:
            raise domain.StateIntegrityError('exact Checkpoint required')
        subject = domain.subject_document(binding, ledger_identity)
        domain._text(reason)
        with self._transaction() as (events, tasks):
            task = tasks.get(checkpoint.task_id)
            if (checkpoint.store_id != self.store_id or checkpoint.project_id != self.project_id
                    or task is None or type(checkpoint.revision) is not int
                    or task.revision != checkpoint.revision
                    or binding.run.contract.task_id != checkpoint.task_id):
                raise domain.StateConflictError('stale or foreign checkpoint')
            if not domain.continuation_eligible(task):
                raise domain.StateConflictError('continuation unsafe')
            if any(run.run_id == binding.run.run_id for t in tasks.values() for run in t.runs):
                raise domain.StateConflictError('new unique Run ID required')
            if self._authorizer is None:
                raise domain.ContinuationDeniedError('fresh authority adapter required')
            request = domain.ContinuationRequest(checkpoint, self._session_nonce,
                secrets.token_hex(32), binding, ledger_identity, reason)
            original = domain.encode(asdict(request))
            try:
                approval = self._authorizer(request)
                if (type(approval) is not domain.ContinuationApproval
                        or domain.encode(asdict(request)) != original
                        or approval.session_nonce != self._session_nonce
                        or approval.request_nonce != request.request_nonce):
                    raise domain.ContinuationDeniedError('fresh exact approval required')
                document = asdict(approval)
                domain._approval(document)
            except Exception:
                raise domain.ContinuationDeniedError('fresh exact approval required') from None
            return self._append(events, tasks, task.task_id, checkpoint.revision, 'continue',
                dict(subject=subject, approval=document, reason=reason))

    def get_task(self, task_id):
        domain._text(task_id)
        with self._transaction() as (_, tasks):
            return tasks.get(task_id)

    def get_run(self, run_id):
        domain._text(run_id)
        with self._transaction() as (_, tasks):
            return next((run for task in tasks.values() for run in task.runs if run.run_id == run_id), None)

    def checkpoint(self, task_id):
        task = self.get_task(task_id)
        if task is None:
            raise domain.StateConflictError('unknown Task')
        return domain.Checkpoint(self.store_id, self.project_id, task_id, task.revision)

    def page(self, *, after='', limit=50, task_id=None):
        if type(after) is not str or type(limit) is not int or not 1 <= limit <= 100:
            raise domain.StateIntegrityError('invalid bounded keyset page')
        with self._transaction() as (_, tasks):
            if task_id is None:
                items = sorted(tasks.values(), key=lambda item: item.task_id)
                return tuple(item for item in items if item.task_id > after)[:limit]
            domain._text(task_id)
            task = tasks.get(task_id)
            items = sorted(task.runs, key=lambda item: item.run_id) if task else []
            return tuple(item for item in items if item.run_id > after)[:limit]

    def close(self):
        with self._mutex:
            if self._pid != os.getpid():
                raise domain.StateConflictError('foreign process Store session')
            if self._active:
                raise domain.StateConflictError('cannot close during Store operation')
            if self._closed:
                return
            self._closed = True
            try:
                if self._connection is not None:
                    self._connection.close()
            finally:
                if self._lock_file is not None:
                    self._lock_file.close()  # Closing releases ownership, including failed opens.
                self._authorizer = None

    def __reduce_ex__(self, protocol):
        raise TypeError('live Store session cannot be serialized')

    def __copy__(self):
        raise TypeError('live Store session cannot be copied')

    def __deepcopy__(self, memo):
        raise TypeError('live Store session cannot be copied')
