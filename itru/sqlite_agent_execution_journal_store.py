"""Dedicated same-host SQLite Journal. No import-time I/O or implicit setup.

Operational open never creates or migrates. Explicit provisioning executes only
the fixed checksummed Journal resource. No authorization-ledger SQL is present.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.resources import files
import os
from pathlib import Path
import re
import sqlite3
import stat

from itru import agent_execution_journal as journal
from itru._sqlite_journal_migrations import SCHEMA_VERSION, RESOURCE_NAME, RESOURCE_SHA256
from itru.authorization_domain_ownership import AuthorizationDomainIdentity

APPLICATION_ID = 0x49544A31


class JournalIncompatibleSchema(journal.JournalIntegrityError):
    pass


@dataclass(frozen=True, slots=True)
class SqliteExecutionJournalConfiguration:
    database_path: Path
    storage_directory: Path
    journal_id: str
    ledger_identity: AuthorizationDomainIdentity
    busy_timeout_ms: int = 5000

    def __setstate__(self, state):
        raise TypeError('Journal configuration cannot be restored in place')


@dataclass(frozen=True, slots=True)
class JournalCursor:
    journal_id: str
    high_water: int
    last_sequence: int = 0

    def __setstate__(self, state):
        raise TypeError('Journal cursor cannot be restored in place')


def _identity(configuration):
    return journal._ledger_document(configuration.ledger_identity)


def _schema_resource():
    raw = files('itru._sqlite_journal_migrations').joinpath(RESOURCE_NAME).read_bytes()
    if hashlib.sha256(raw).hexdigest() != RESOURCE_SHA256:
        raise JournalIncompatibleSchema()
    text = raw.decode('utf-8')
    statements, pending = [], ''
    for line in text.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statements.append(pending.strip())
            pending = ''
    if pending.strip() or not statements:
        raise JournalIncompatibleSchema()
    expected = []
    for statement in statements:
        match = re.match(r'CREATE (TABLE|TRIGGER) ([a-z_]+)\b', statement)
        if match is None:
            raise JournalIncompatibleSchema()
        expected.append((match[2], match[1].lower(), statement.rstrip(';')))
    return statements, tuple(sorted(expected))


def _plain(path, *, directory):
    item = path.lstat()
    if (item.st_mode & 0o170000) != (stat.S_IFDIR if directory else stat.S_IFREG):
        raise OSError('unsupported Journal storage object')
    if getattr(item, 'st_file_attributes', 0) & (0x400 | 0x1000 | 0x40000 | 0x400000) or path.is_symlink():
        raise OSError('Journal reparse storage rejected')
    if not directory and item.st_nlink != 1:
        raise OSError('Journal hard-linked storage rejected')
    return (item.st_dev, item.st_ino)


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
            raise OSError('Journal security profile rejected')
    else:
        raise OSError('unsupported Journal storage profile')


def _configuration(configuration, *, require_file):
    if type(configuration) is not SqliteExecutionJournalConfiguration:
        raise journal.JournalIntegrityError()
    c = configuration
    journal._text(c.journal_id); _identity(c)
    journal._integer(c.busy_timeout_ms, 1, 60000)
    if (type(c.database_path) is not Path and not isinstance(c.database_path, Path)) or not isinstance(c.storage_directory, Path):
        raise journal.JournalIntegrityError()
    if (not c.database_path.is_absolute() or not c.storage_directory.is_absolute()
            or c.database_path.parent != c.storage_directory
            or c.database_path.resolve(strict=False) != c.database_path
            or c.storage_directory.resolve(strict=True) != c.storage_directory
            or '..' in c.database_path.parts or str(c.database_path).startswith('\\\\')):
        raise OSError('Journal path is not exact local storage')
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise OSError('unsupported SQLite version')
    for parent in (c.storage_directory, *c.storage_directory.parents):
        _plain(parent, directory=True)
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        function = kernel.GetDriveTypeW
        function.argtypes, function.restype = [ctypes.c_wchar_p], ctypes.c_uint
        if function(c.database_path.anchor) != 3:
            raise OSError('Journal requires a fixed local volume')
    _security(c.storage_directory, directory=True)
    if require_file:
        _plain(c.database_path, directory=False)
        _security(c.database_path, directory=False)
    for suffix in ('-wal', '-shm', '-journal'):
        sidecar = Path(str(c.database_path) + suffix)
        if sidecar.exists() or sidecar.is_symlink():
            _plain(sidecar, directory=False)
            _security(sidecar, directory=False)


def _rollback(connection):
    if connection is not None:
        try:
            connection.execute('ROLLBACK')
        except sqlite3.Error:
            pass


class SqliteExecutionJournalStore:
    """Configured trusted writer; raw JSON import and effect replay unsupported."""
    def __init__(self, configuration, *, clock=None):
        _configuration(configuration, require_file=True)
        self.configuration = configuration
        self._clock = clock if clock is not None else (lambda: datetime.now(timezone.utc))
        self._path_identity = _plain(configuration.database_path, directory=False)
        self._directory_identity = _plain(configuration.storage_directory, directory=True)
        with self._snapshot() as connection:
            self._verify(connection)

    @classmethod
    def provision(cls, configuration, *, metadata_authorized=False):
        """Explicit new Journal only. Caller provisions the owned directory first."""
        if metadata_authorized is not True:
            raise journal.JournalIntegrityError()
        _configuration(configuration, require_file=False)
        statements, ignored = _schema_resource()
        fd = os.open(configuration.database_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        _security(configuration.database_path, directory=False, establish=True)
        connection = None
        try:
            connection = sqlite3.connect(configuration.database_path.as_uri() + '?mode=rw',
                uri=True, isolation_level=None, timeout=configuration.busy_timeout_ms / 1000)
            connection.execute('PRAGMA foreign_keys=ON')
            if connection.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
                raise OSError('Journal WAL unavailable')
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('BEGIN IMMEDIATE')
            for statement in statements:
                connection.execute(statement)
            identity = _identity(configuration)
            connection.execute('INSERT INTO journal_metadata VALUES (1,?,?,?,?,1,?)',
                (configuration.journal_id, identity['authorization_domain_id'], identity['ledger_instance_id'],
                 str(identity['domain_generation']), RESOURCE_SHA256))
            connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
            connection.execute('COMMIT')
        except BaseException:
            _rollback(connection)
            # A partially provisioned file is retained for explicit administration.
            # Operational open must reject it; there is no automatic repair/delete.
            raise
        finally:
            if connection is not None:
                connection.close()
        return cls(configuration)

    def _connect(self, *, readonly=False):
        c = self.configuration
        _configuration(c, require_file=True)
        if (_plain(c.database_path, directory=False) != self._path_identity
                or _plain(c.storage_directory, directory=True) != self._directory_identity):
            raise journal.JournalIntegrityError()
        connection = sqlite3.connect(c.database_path.as_uri() + ('?mode=ro' if readonly else '?mode=rw'),
            uri=True, isolation_level=None, timeout=c.busy_timeout_ms / 1000)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('PRAGMA recursive_triggers=ON')
            if readonly:
                connection.execute('PRAGMA query_only=ON')
            if (connection.execute('PRAGMA journal_mode').fetchone()[0].lower() != 'wal'
                    or connection.execute('PRAGMA synchronous').fetchone()[0] != 2
                    or connection.execute('PRAGMA foreign_keys').fetchone()[0] != 1):
                raise OSError('Journal durability profile rejected')
            return connection
        except BaseException:
            connection.close()
            raise

    def _snapshot(self):
        from contextlib import contextmanager
        @contextmanager
        def snapshot():
            connection = self._connect(readonly=True)
            try:
                connection.execute('BEGIN')
                yield connection
            finally:
                _rollback(connection)
                connection.close()
        return snapshot()

    def _verify(self, connection):
        if (connection.execute('PRAGMA application_id').fetchone()[0] != APPLICATION_ID
                or connection.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION):
            raise JournalIncompatibleSchema()
        ignored, expected = _schema_resource()
        schema = tuple(sorted(tuple(row) for row in connection.execute(
            "SELECT name,type,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'")))
        if schema != expected:
            raise JournalIncompatibleSchema()
        if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise journal.JournalIntegrityError()
        metadata = connection.execute('SELECT * FROM journal_metadata').fetchall()
        c, identity = self.configuration, _identity(self.configuration)
        wanted = (1, c.journal_id, identity['authorization_domain_id'], identity['ledger_instance_id'],
                  str(identity['domain_generation']), SCHEMA_VERSION, RESOURCE_SHA256)
        if len(metadata) != 1 or tuple(metadata[0]) != wanted:
            raise journal.JournalIntegrityError()
        records, facts, subjects, runs, previous_time = [], {}, {}, {}, None
        for row in connection.execute('SELECT * FROM journal_entries ORDER BY sequence'):
            document = journal._validate_record(journal._decode(row['record_json']))
            key = journal._subject_key(document)
            index = (document['sequence'], journal._encode(list(key)), document['event_kind'], document['recorded_at'], row['record_json'])
            if (tuple(row) != index or document['journal_id'] != c.journal_id
                    or document['ledger_identity'] != identity or document['sequence'] != len(records) + 1
                    or (previous_time is not None and journal._time(document['recorded_at']) < previous_time)):
                raise journal.JournalIntegrityError()
            fact_key = (key, document['event_kind'])
            subject = journal._subject_only(document)
            run = document['admission']['grant']['run']
            if (fact_key in facts or (key in subjects and subjects[key] != subject)
                    or (run['run_id'] in runs and runs[run['run_id']] != run['contract'])
                    or (document['event_kind'] == 'result_observed' and (key, 'entry_observed') not in facts)):
                raise journal.JournalIntegrityError()
            record = journal.JournalRecord(row['record_json'])
            facts[fact_key], subjects[key], runs[run['run_id']] = record, subject, run['contract']
            previous_time = journal._time(document['recorded_at'])
            records.append(record)
        return tuple(records), facts, subjects, runs, previous_time

    def _fault(self, point):
        """Private fault-injection edge; no configured/public callback registry."""

    def append(self, observations):
        connection, commit_attempted, subject_key, kinds = None, False, (), ()
        try:
            if type(observations) is not tuple or not observations or len(observations) > 2:
                raise journal.JournalIntegrityError()
            if not all(journal._trusted_fact(item) for item in observations):
                raise journal.JournalIntegrityError()
            bodies = [journal._validate_body(journal._decode(item.body_json)) for item in observations]
            subject_key, kinds = journal._subject_key(bodies[0]), tuple(item['event_kind'] for item in bodies)
            if (len(set(kinds)) != len(kinds) or any(journal._subject_key(item) != subject_key
                    or journal._subject_only(item) != journal._subject_only(bodies[0]) for item in bodies)):
                raise journal.JournalIntegrityError()
            if any(item['ledger_identity'] != _identity(self.configuration) for item in bodies):
                raise journal.JournalIntegrityError()
            connection = self._connect()
            connection.execute('BEGIN IMMEDIATE')
            records, facts, subjects, runs, last_time = self._verify(connection)
            result, additions = [], []
            for body in bodies:
                prior = facts.get((subject_key, body['event_kind']))
                if prior is not None:
                    prior_body = {key: prior.document[key] for key in journal._BODY_KEYS}
                    if prior_body != body:
                        return journal.JournalReceipt('conflict', subject_key, kinds)
                    result.append(prior)
                else:
                    run = body['admission']['grant']['run']
                    if ((subject_key in subjects and subjects[subject_key] != journal._subject_only(body))
                            or (run['run_id'] in runs and runs[run['run_id']] != run['contract'])):
                        return journal.JournalReceipt('conflict', subject_key, kinds)
                    additions.append(body)
            if not additions:
                return journal.JournalReceipt('existing', subject_key, kinds, tuple(result))
            if len(records) + len(additions) > journal.MAX_SEQUENCE:
                raise journal.JournalIntegrityError()
            try:
                stamp = journal._clock_text(self._clock())
                if last_time is not None and journal._time(stamp) < last_time:
                    raise journal.JournalIntegrityError()
            except Exception:
                return journal.JournalReceipt('clock_failure', subject_key, kinds)
            for body in additions:
                sequence = len(records) + 1
                document = dict(body, journal_id=self.configuration.journal_id, sequence=sequence, recorded_at=stamp)
                encoded = journal._encode(journal._validate_record(document))
                self._fault('append.before_insert')
                connection.execute('INSERT INTO journal_entries VALUES (?,?,?,?,?)',
                    (sequence, journal._encode(list(subject_key)), body['event_kind'], stamp, encoded))
                record = journal.JournalRecord(encoded)
                result.append(record); records = (*records, record)
                self._fault('append.after_insert')
            self._verify(connection)
            if not all(journal._trusted_fact(item) for item in observations):
                raise journal.JournalIntegrityError()
            self._fault('append.before_commit')
            commit_attempted = True
            connection.execute('COMMIT')
            self._fault('append.after_commit_before_response')
            return journal.JournalReceipt('appended', subject_key, kinds,
                tuple(sorted(result, key=lambda item: item.document['sequence'])))
        except Exception as error:
            if commit_attempted:
                outcome = 'commit_unknown'
            elif isinstance(error, journal.JournalMetadataLimit):
                outcome = 'metadata_limit'
            elif isinstance(error, JournalIncompatibleSchema):
                outcome = 'incompatible_schema'
            elif isinstance(error, (journal.JournalIntegrityError, ValueError, TypeError, UnicodeError, sqlite3.IntegrityError)):
                outcome = 'integrity_failure'
            else:
                outcome = 'storage_unavailable'
            return journal.JournalReceipt(outcome, subject_key, kinds)
        finally:
            _rollback(connection)
            if connection is not None:
                connection.close()

    def lookup(self, subject_identity, *, subject=None):
        if type(subject_identity) is not tuple or len(subject_identity) != 5:
            raise journal.JournalIntegrityError()
        for item in subject_identity:
            journal._text(item)
        identity = _identity(self.configuration)
        if subject_identity[:2] != (identity['ledger_instance_id'], identity['authorization_domain_id']):
            raise journal.JournalIntegrityError()
        with self._snapshot() as connection:
            records = self._verify(connection)[0]
            found = tuple(item for item in records if journal._subject_key(item.document) == subject_identity)
            if subject is not None and any(journal._subject_only(item.document) != subject for item in found):
                raise journal.JournalIntegrityError()
            return found

    def page(self, *, cursor=None, limit=100):
        journal._integer(limit, 1, 1000)
        with self._snapshot() as connection:
            records = self._verify(connection)[0]
            if cursor is None:
                cursor = JournalCursor(self.configuration.journal_id, len(records))
            if (type(cursor) is not JournalCursor or cursor.journal_id != self.configuration.journal_id
                    or type(cursor.high_water) is not int or type(cursor.last_sequence) is not int
                    or not 0 <= cursor.last_sequence <= cursor.high_water <= len(records)):
                raise journal.JournalIntegrityError()
            page = tuple(item for item in records
                if cursor.last_sequence < item.document['sequence'] <= cursor.high_water)[:limit]
            last = page[-1].document['sequence'] if page else cursor.last_sequence
            return page, JournalCursor(cursor.journal_id, cursor.high_water, last)
