"""Sixty fresh AIO-055 production scenarios on isolated, non-dispatching ledgers.

Only exact unittest module/node selection is supported. All resources are
invocation-owned temporary SQLite/registry fixtures. Subprocesses are storage
crash/restart probes, never workers. Abstract operation resources are never
opened, inspected, or invoked. Corruption is confined to closed disposable
connections; no supported operational path seeds or repairs durable history.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

import engineering_orchestration as package
import engineering_orchestration.sqlite_agent_execution_dispatch_admission_store as subject
from engineering_orchestration.agent_execution_dispatch_admission import AgentExecutionDispatchAdmission
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    _mint_admission_request, _mint_guarded_history_request, _mint_revocation_request,
)
from tests import test_sqlite_agent_execution_dispatch_admission_store as fixture
from tests import test_local_operational_trust as integrated

ROOT = Path(__file__).resolve().parent.parent
V1_CHECKSUM = "6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed"
V1_FINGERPRINT = "de080810b1d644dacf53e6bf79cbbd01343344904397a91c6dd483bd48dfad46"
INTENTS = "agent_execution_dispatch_intents"
MARKERS = "legacy_admission_markers"
ADMISSIONS = "agent_execution_dispatch_admissions"
_PROCESS_EVIDENCE = []
_MIGRATION_CUTS = frozenset({
    "migration.before_transaction", "migration.after_begin", "migration.after_dirty",
    "migration.after_schema", "migration.after_legacy_population",
    "migration.after_clean_transition", "migration.before_commit",
    "migration.after_commit_before_response",
})
_ADMISSION_CUTS = frozenset({
    "before_transaction", "after_begin", "after_checks", "before_admission_insert",
    "after_admission_insert_before_intent", "after_intent_insert_before_watermark",
    "after_insert_before_commit", "after_watermark_before_commit", "before_commit",
    "after_commit_before_response",
})


def _connect(path: Path):
    connection = sqlite3.connect(path, isolation_level=None, timeout=2)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _request(configuration, grant, binding):
    return _mint_admission_request(configuration.authorization_domain_id, grant, binding, grant.run)


def _history(configuration, grant, binding):
    return _mint_guarded_history_request(configuration.authorization_domain_id, grant, binding)


def _make_v1(configuration, *, nonempty=True, reset=False):
    """Build genuine preserved-v1 history only in closed disposable setup."""
    data = (ROOT / "engineering_orchestration/_sqlite_admission_migrations/0001_initial.sql").read_bytes()
    if hashlib.sha256(data).hexdigest() != V1_CHECKSUM:
        raise AssertionError("the preserved production v1 migration changed")
    records = []
    with closing(_connect(configuration.database_path)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        if reset:
            connection.execute("PRAGMA foreign_keys=OFF")
            for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='trigger'").fetchall():
                connection.execute('DROP TRIGGER "' + row[0].replace('"', '""') + '"')
            for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND substr(name, 1, 7) <> 'sqlite_'").fetchall():
                connection.execute('DROP TABLE "' + row[0].replace('"', '""') + '"')
            connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        for statement in subject._sql_statements(data):
            connection.execute(statement)
        connection.execute("INSERT INTO admission_schema_migrations VALUES (1, '0001_initial.sql', ?)", (V1_CHECKSUM,))
        manifest = hashlib.sha256(f"1:0001_initial.sql:{V1_CHECKSUM}".encode()).hexdigest()
        connection.execute(
            "INSERT INTO admission_ledger_metadata VALUES (1, ?, ?, ?, 1, ?, ?, ?, 'active', 'clean', 1, NULL, NULL)",
            (subject.STORE_ID, subject.SQLITE_APPLICATION_ID, configuration.authorization_domain_id,
             manifest, configuration.ledger_instance_id, configuration.domain_generation),
        )
        connection.execute(f"PRAGMA application_id={subject.SQLITE_APPLICATION_ID}")
        connection.execute("PRAGMA user_version=1")
        if nonempty:
            _, decision_text, decision_key = subject._canonical_decision_time(fixture.DECISION_TIME)
            for index in range(2):
                run = fixture.make_run(f"run::aio055-legacy-{index}")
                grant = fixture.make_grant(bound_run=run, grant_id=f"grant::aio055-legacy-{index}", domain_id=configuration.authorization_domain_id)
                binding = fixture.make_binding(bound_run=run)
                admission = AgentExecutionDispatchAdmission(grant, binding, decision_text)
                connection.execute(
                    "INSERT INTO agent_execution_dispatch_admissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*subject._grant_identity(grant), run.run_id, subject._encode_grant(grant),
                     subject._encode_binding(binding), subject._encode_admission(admission), decision_text, decision_key),
                )
                records.append(admission)
            connection.execute("UPDATE admission_ledger_metadata SET last_decision_time=?, last_decision_time_key=?", (decision_text, decision_key))
        connection.execute("COMMIT")
        if subject._schema_fingerprint(connection) != V1_FINGERPRINT:
            raise AssertionError("the disposable fixture is not the exact v1 schema")
    return records


def _seed_v1_revocation(configuration, grant):
    """Append valid old revocation solely during closed legacy-fixture setup."""
    _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME + timedelta(minutes=1))
    with closing(_connect(configuration.database_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO agent_execution_grant_revocations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*subject._grant_identity(grant), grant.run.run_id, subject._encode_grant(grant),
             grant.issuer_kind, grant.issuer_id, text, key))
        connection.execute("UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?", (text, key))
        connection.execute("COMMIT")


def _snapshot(path):
    with closing(_connect(path)) as connection:
        schema = tuple(tuple(row) for row in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"))
        rows = []
        for table in ("admission_ledger_metadata", "admission_schema_migrations", ADMISSIONS,
                      "agent_execution_grant_revocations", INTENTS, MARKERS):
            if connection.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?", (table,)).fetchone():
                rows.append((table, tuple(sorted(tuple(row) for row in connection.execute('SELECT * FROM "' + table + '"')))))
        return schema, tuple(rows), connection.execute("PRAGMA user_version").fetchone()[0], connection.execute("PRAGMA application_id").fetchone()[0]


def _child_probe(root_text, path_text, operation, cut, nonce):
    """Closed-set process entry; validate owned target before any ledger I/O."""
    root = Path(root_text).resolve(strict=True)
    path = Path(path_text)
    if (root.parent != Path(tempfile.gettempdir()).resolve() or not root.name.startswith("aio-055-")
            or not (root / ".aio055-owner").is_file() or path.parent.resolve() != root
            or (root / ".aio055-owner").read_text(encoding="ascii") != nonce):
        raise AssertionError("storage child target is outside its invocation-owned root")
    configuration = fixture.config_for(path)
    if operation == "admit":
        if cut not in _ADMISSION_CUTS:
            raise AssertionError("unknown admission crash cut")
        class CrashStore(subject.SqliteAgentExecutionDispatchAdmissionStore):
            def _fault(self, point):
                if point == cut:
                    os._exit(73)
        store = CrashStore(configuration, clock=fixture.MutableClock(), access=fixture.store_access(configuration))
        grant = fixture.make_grant()
        store.admit_or_return_existing(_request(configuration, grant, fixture.make_binding()))
        raise AssertionError("the requested Admission crash cut was not reached")
    if operation == "migrate":
        if cut not in _MIGRATION_CUTS:
            raise AssertionError("unknown migration crash cut")
        class CrashMigration(subject.SqliteAgentExecutionDispatchAdmissionStore):
            @classmethod
            def _administration_fault(cls, point):
                if point == cut:
                    os._exit(73)
        CrashMigration.migrate(configuration, access=fixture.administration_access(configuration))
        raise AssertionError("the requested migration crash cut was not reached")
    if operation == "restart" and cut == "none":
        store = subject.SqliteAgentExecutionDispatchAdmissionStore(configuration, clock=fixture.MutableClock(RuntimeError("history clock forbidden")), access=fixture.store_access(configuration))
        grant = fixture.make_grant()
        result = store.admit_or_return_existing(_request(configuration, grant, fixture.make_binding()))
        with closing(_connect(path)) as connection:
            count = connection.execute(f"SELECT count(*) FROM {INTENTS}").fetchone()[0]
        print(json.dumps({"outcome": result.outcome.value, "intents": count, "clock_calls": store._clock.calls}))
        return
    if operation == "timeout" and cut == "none":
        import time
        time.sleep(30)
        return
    raise AssertionError("unknown child operation")


class AtomicDurableDispatchOutboxTests(unittest.TestCase):
    def setUp(self):
        self.parent = Path(tempfile.gettempdir()).resolve()
        self.root = Path(tempfile.mkdtemp(prefix="aio-055-", dir=self.parent)).resolve()
        self.nonce = uuid.uuid4().hex
        (self.root / ".aio055-owner").write_text(self.nonce, encoding="ascii")
        self.addCleanup(self._cleanup_root)
        self.configuration = fixture.config_for(self.root / "outbox.sqlite3")
        self.clock = fixture.MutableClock()
        self.grant = fixture.make_grant()
        self.binding = fixture.make_binding()

    def _cleanup_root(self):
        if (self.root.is_symlink() or self.root.is_junction() or self.root.resolve() != self.root
                or self.root.parent != self.parent
                or (self.root / ".aio055-owner").read_text(encoding="ascii") != self.nonce):
            raise AssertionError("refusing cleanup outside the exact nonce-marked root")
        shutil.rmtree(self.root)

    def _configuration(self, suffix):
        return fixture.config_for(self.root / (suffix + ".sqlite3"))

    def _provision(self, configuration=None, *, clock=None, store_type=None, **kwargs):
        configuration = configuration or self.configuration
        result = subject.SqliteAgentExecutionDispatchAdmissionStore.provision(configuration, access=fixture.administration_access(configuration))
        self.assertEqual(result.outcome.value, "provisioned", result.detail)
        return self._open(configuration, clock=clock, store_type=store_type, **kwargs)

    def _open(self, configuration=None, *, clock=None, store_type=None, **kwargs):
        configuration = configuration or self.configuration
        return (store_type or subject.SqliteAgentExecutionDispatchAdmissionStore)(configuration, clock=clock or self.clock, access=fixture.store_access(configuration), **kwargs)

    def _migrate(self, configuration=None, *, store_type=None):
        configuration = configuration or self.configuration
        return (store_type or subject.SqliteAgentExecutionDispatchAdmissionStore).migrate(configuration, access=fixture.administration_access(configuration))

    def _counts(self, configuration=None):
        configuration = configuration or self.configuration
        with closing(_connect(configuration.database_path)) as connection:
            return tuple(connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in (ADMISSIONS, INTENTS, MARKERS))

    def _admit(self, store, *, grant=None, binding=None):
        return store.admit_or_return_existing(_request(store.configuration, grant or self.grant, binding or self.binding))

    def _assert_outcome(self, result, expected):
        self.assertEqual(result.outcome.value, expected, result.detail)

    def _corrupt(self, configuration, mutation):
        """Temporarily suspend guards solely on a closed corruption fixture."""
        with closing(_connect(configuration.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute("PRAGMA ignore_check_constraints=ON")
            triggers = connection.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' ORDER BY name").fetchall()
            connection.execute("BEGIN IMMEDIATE")
            for name, _ in triggers:
                connection.execute('DROP TRIGGER "' + name.replace('"', '""') + '"')
            mutation(connection)
            for _, statement in triggers:
                connection.execute(statement)
            connection.execute("COMMIT")

    def _reject_open(self, configuration):
        with self.assertRaises((subject.SqliteAdmissionStoreIntegrityError, subject.SqliteAdmissionStoreIncompatibleSchemaError)):
            self._open(configuration)

    def _assert_classification(self, configuration, admission, expected):
        store = self._open(configuration)
        with closing(store._open_existing(allow_fenced=False)) as connection:
            value = store._classify_admission_dispatch(connection, admission)
        self.assertEqual(value.kind, expected)
        self.assertEqual(value.admission, admission)
        with self.assertRaises((AttributeError, TypeError)):
            value.kind = "rebound"
        return value

    def _run_child(self, configuration, operation, cut, *, expected_exit=73, timeout=20):
        self.assertEqual(configuration.database_path.parent.resolve(), self.root)
        source = "import sys,types; sys.path.insert(0, sys.argv[1]); tests=types.ModuleType('tests'); tests.__path__=[sys.argv[1]+'/tests']; sys.modules['tests']=tests; from tests.test_atomic_durable_dispatch_outbox import _child_probe; _child_probe(*sys.argv[2:])"
        command = [sys.executable, "-I", "-B", "-c", source, str(ROOT), str(self.root), str(configuration.database_path), operation, cut, self.nonce]
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP") if key in os.environ}
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=self.root, env=environment, shell=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timed_out = False
        try:
            try:
                output, errors = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                output, errors = process.communicate(timeout=15)
            if operation != "timeout":
                self.assertFalse(timed_out, "owned storage probe timed out")
                self.assertEqual(process.returncode, expected_exit, errors.decode(errors="replace"))
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=15)
            for handle in (process.stdout, process.stderr):
                if handle is not None:
                    handle.close()
            native_handle = getattr(process, "_handle", None)
            if native_handle is not None:
                native_handle.Close()
            _PROCESS_EVIDENCE.append({"mode": operation, "exit": process.returncode, "timeout": timed_out,
                "reaped": process.poll() is not None, "pipes_closed": process.stdout.closed and process.stderr.closed,
                "shell": False, "root": str(self.root), "environment": tuple(sorted(environment))})
        if operation == "timeout":
            self.assertTrue(timed_out)
        return output

    def _migration_crash(self, cut):
        _make_v1(self.configuration)
        before = _snapshot(self.configuration.database_path)
        self._run_child(self.configuration, "migrate", cut)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self._reject_open(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        self.assertEqual(self._counts(), (2, 0, 2))

    def _admission_crash(self, cut):
        self._provision()
        self._run_child(self.configuration, "admit", cut)
        store = self._open()
        self.assertEqual(self._counts(), (0, 0, 0))
        self.assertEqual(store.watermark(), (None, None))
        self._assert_outcome(self._admit(store), "newly_admitted")
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O01_empty_v1_migration(self):
        _make_v1(self.configuration, nonempty=False)
        self._reject_open(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        self.assertEqual(self._counts(), (0, 0, 0))
        self.assertEqual(self._open().watermark(), (None, None))

        fresh = self._configuration("fresh-v2-empty")
        self._provision(fresh)
        self.assertEqual(self._counts(fresh), (0, 0, 0))
        self.assertEqual(self._open(fresh).watermark(), (None, None))

    def test_O02_nonempty_v1_migration(self):
        records = _make_v1(self.configuration)
        _seed_v1_revocation(self.configuration, records[0].grant)
        prior_revocations = dict(_snapshot(self.configuration.database_path)[1])["agent_execution_grant_revocations"]
        self._assert_outcome(self._migrate(), "migrated")
        self.assertEqual(self._counts(), (2, 0, 2))
        self.assertEqual(dict(_snapshot(self.configuration.database_path)[1])["agent_execution_grant_revocations"], prior_revocations)
        for admission in records:
            self._assert_classification(self.configuration, admission, "legacy")
        with closing(_connect(self.configuration.database_path)) as connection:
            self.assertEqual([row[0] for row in connection.execute(f"SELECT migration_id FROM {MARKERS}")], [2, 2])

    def test_O03_no_historical_intent_backfill(self):
        records = _make_v1(self.configuration)
        old_rows = dict(_snapshot(self.configuration.database_path)[1])[ADMISSIONS]
        self._assert_outcome(self._migrate(), "migrated")
        self.assertEqual(dict(_snapshot(self.configuration.database_path)[1])[ADMISSIONS], old_rows)
        self.assertEqual(self._counts(), (len(records), 0, len(records)))

    def test_O04_atomic_migration_publication(self):
        _make_v1(self.configuration)
        with closing(_connect(self.configuration.database_path)) as reader:
            reader.execute("BEGIN")
            self.assertEqual(reader.execute("PRAGMA user_version").fetchone()[0], 1)
            observations = []
            def observe(point):
                if point in {"migration.after_schema", "migration.after_legacy_population", "migration.before_commit"}:
                    observations.append(reader.execute("PRAGMA user_version").fetchone()[0])
                    self.assertIsNone(reader.execute("SELECT 1 FROM sqlite_schema WHERE name=?", (INTENTS,)).fetchone())
            with patch.object(subject.SqliteAgentExecutionDispatchAdmissionStore, "_administration_fault", side_effect=observe):
                self._assert_outcome(self._migrate(), "migrated")
            self.assertEqual(observations, [1, 1, 1])
            self.assertEqual(reader.execute("PRAGMA user_version").fetchone()[0], 1)
            reader.execute("COMMIT")
            self.assertEqual(reader.execute("PRAGMA user_version").fetchone()[0], subject.SCHEMA_VERSION)
        self.assertEqual(self._counts(), (2, 0, 2))

    def test_O05_migration_crash_before_transaction(self):
        self._migration_crash("migration.before_transaction")

    def test_O06_migration_crash_after_ddl(self):
        self._migration_crash("migration.after_schema")

    def test_O07_migration_crash_after_marker_population(self):
        self._migration_crash("migration.after_legacy_population")

    def test_O08_migration_crash_before_commit(self):
        self._migration_crash("migration.before_commit")

    def test_O09_migration_response_loss(self):
        for index, (cut, outcome, retry) in enumerate((
                ("migration.before_commit", "migration_failure", "migrated"),
                ("migration.after_commit_before_response", "commit_unknown", "already_current"))):
            with self.subTest(cut=cut):
                configuration = self._configuration(f"migration-response-{index}")
                _make_v1(configuration)
                before = _snapshot(configuration.database_path)
                def lose(point):
                    if point == cut:
                        raise OSError("synthetic migration response loss")
                with patch.object(subject.SqliteAgentExecutionDispatchAdmissionStore, "_administration_fault", side_effect=lose):
                    self._assert_outcome(self._migrate(configuration), outcome)
                if retry == "migrated":
                    self.assertEqual(_snapshot(configuration.database_path), before)
                self._assert_outcome(self._migrate(configuration), retry)
                self.assertEqual(self._counts(configuration), (2, 0, 2))
                with closing(_connect(configuration.database_path)) as connection:
                    self.assertEqual(connection.execute("SELECT count(*) FROM admission_schema_migrations").fetchone()[0], subject.SCHEMA_VERSION)

    def test_O10_migration_one_checksum_mismatch(self):
        _make_v1(self.configuration)
        self._corrupt(self.configuration, lambda c: c.execute("UPDATE admission_schema_migrations SET sha256=? WHERE migration_id=1", ("0" * 64,)))
        before = _snapshot(self.configuration.database_path)
        self._assert_outcome(self._migrate(), "integrity_failure")
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O11_packaged_migration_two_checksum_mismatch(self):
        _make_v1(self.configuration)
        before = _snapshot(self.configuration.database_path)
        migrations = (subject.MIGRATIONS[0], replace(subject.MIGRATIONS[1], sha256="0" * 64))
        with patch.object(subject, "MIGRATIONS", migrations):
            self._assert_outcome(self._migrate(), "migration_failure")
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O12_source_fingerprint_mismatch(self):
        mutations = ("CREATE TABLE extra_source (value TEXT)",
                     "DROP TRIGGER agent_execution_dispatch_admissions_no_delete",
                     "ALTER TABLE agent_execution_dispatch_admissions ADD COLUMN unexpected TEXT")
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=mutation):
                configuration = self._configuration(f"source-fingerprint-{index}")
                _make_v1(configuration)
                with closing(_connect(configuration.database_path)) as connection:
                    connection.execute(mutation)
                before = _snapshot(configuration.database_path)
                self._assert_outcome(self._migrate(configuration), "integrity_failure")
                self.assertEqual(_snapshot(configuration.database_path), before)

    def test_O13_destination_fingerprint_mismatch(self):
        _make_v1(self.configuration)
        before = _snapshot(self.configuration.database_path)
        original = subject._schema_fingerprint
        def wrong_destination(connection):
            return "0" * 64 if connection.execute("PRAGMA user_version").fetchone()[0] == subject.SCHEMA_VERSION else original(connection)
        with patch.object(subject, "_schema_fingerprint", side_effect=wrong_destination):
            self._assert_outcome(self._migrate(), "integrity_failure")
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self._assert_outcome(self._migrate(), "migrated")
        with closing(_connect(self.configuration.database_path)) as connection:
            connection.execute("CREATE TABLE extra_destination (value TEXT)")
        self._reject_open(self.configuration)

    def test_O14_history_prefix_gap_rebound_extra_changed_reordered(self):
        mutations = {
            "gap": lambda c: c.execute("DELETE FROM admission_schema_migrations WHERE migration_id=1"),
            "rebound": lambda c: c.execute("UPDATE admission_schema_migrations SET resource_name='rebound.sql' WHERE migration_id=1"),
            "extra": lambda c: c.execute("INSERT INTO admission_schema_migrations VALUES (?, 'unknown.sql', ?)", (subject.SCHEMA_VERSION + 1, "a" * 64)),
            "changed": lambda c: c.execute("UPDATE admission_schema_migrations SET sha256=? WHERE migration_id=2", ("a" * 64,)),
            "reordered": lambda c: (c.execute("UPDATE admission_schema_migrations SET resource_name='temporary.sql' WHERE migration_id=1"),
                                      c.execute("UPDATE admission_schema_migrations SET resource_name='0001_initial.sql' WHERE migration_id=2"),
                                      c.execute("UPDATE admission_schema_migrations SET resource_name='0002_dispatch_outbox.sql' WHERE migration_id=1")),
        }
        for name, mutation in mutations.items():
            with self.subTest(branch=name):
                configuration = self._configuration("history-" + name)
                self._provision(configuration)
                self._corrupt(configuration, mutation)
                before = _snapshot(configuration.database_path)
                self._reject_open(configuration)
                self._assert_outcome(self._migrate(configuration), "integrity_failure")
                self.assertEqual(_snapshot(configuration.database_path), before)

    def test_O15_unknown_newer_schema(self):
        self._provision()
        with closing(_connect(self.configuration.database_path)) as connection:
            connection.execute(f"PRAGMA user_version={subject.SCHEMA_VERSION + 1}")
        before = _snapshot(self.configuration.database_path)
        self._reject_open(self.configuration)
        self._assert_outcome(self._migrate(), "incompatible_schema")
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O16_dirty_or_partial_schema(self):
        for version, branch in ((1, "dirty"), (2, "dirty"), (1, "partial"), (2, "partial")):
            with self.subTest(version=version, branch=branch):
                configuration = self._configuration(f"{branch}-{version}")
                if version == 1:
                    _make_v1(configuration)
                else:
                    self._provision(configuration)
                with closing(_connect(configuration.database_path)) as connection:
                    if branch == "dirty":
                        connection.execute("UPDATE admission_ledger_metadata SET migration_state='dirty'")
                    elif version == 1:
                        connection.execute("CREATE TABLE legacy_admission_markers (grant_id TEXT)")
                    else:
                        connection.execute(f"DROP TABLE {INTENTS}")
                before = _snapshot(configuration.database_path)
                self._reject_open(configuration)
                self._assert_outcome(self._migrate(configuration), "integrity_failure")
                self.assertEqual(_snapshot(configuration.database_path), before)

    def test_O17_application_user_metadata_version_disagreement(self):
        mutations = {
            "application": lambda c: c.execute("PRAGMA application_id=123"),
            "user": lambda c: c.execute("PRAGMA user_version=2"),
            "metadata": lambda c: c.execute("UPDATE admission_ledger_metadata SET schema_version=2"),
        }
        for name, mutation in mutations.items():
            with self.subTest(branch=name):
                configuration = self._configuration("version-" + name)
                _make_v1(configuration)
                self._corrupt(configuration, mutation)
                before = _snapshot(configuration.database_path)
                self._assert_outcome(self._migrate(configuration), "incompatible_schema" if name == "application" else "integrity_failure")
                self._reject_open(configuration)
                self.assertEqual(_snapshot(configuration.database_path), before)

    def test_O18_exact_current_v2_administrative_retry(self):
        _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        before = _snapshot(self.configuration.database_path)
        self._assert_outcome(self._migrate(), "already_current")
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O19_wrong_missing_admin_authority_or_file_pin(self):
        _make_v1(self.configuration)
        before = _snapshot(self.configuration.database_path)
        wrong_configuration = replace(self.configuration, ledger_instance_id="wrong-instance")
        for access in (None, object(), fixture.administration_access(wrong_configuration), fixture.store_access(self.configuration)):
            with self.subTest(access=type(access).__name__):
                result = subject.SqliteAgentExecutionDispatchAdmissionStore.migrate(self.configuration, access=access)
                self.assertNotIn(result.outcome.value, {"migrated", "already_current"})
                self.assertEqual(_snapshot(self.configuration.database_path), before)
        harness = integrated._WindowsHarness(self)
        harness.close()
        original = integrated.windows_owner._verify_binding_ledger
        def reject_pin(*args, **kwargs):
            raise integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError("synthetic missing exact file pin")
        admin = integrated.windows_owner.WindowsLocalAuthorizationDomainAdministration(clock=harness.clock)
        with patch.object(integrated.windows_owner, "_verify_binding_ledger", side_effect=reject_pin):
            with self.assertRaises(integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError):
                admin.migrate(harness.domain_id)
        self.assertIs(integrated.windows_owner._verify_binding_ledger, original)

    def test_O20_new_owned_admission(self):
        harness = integrated._WindowsHarness(self)
        run = integrated._make_run("run::aio055-owned-new")
        principal, proof = harness.human_authority(run)
        result = harness.coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
        self._assert_outcome(result, "newly_admitted")
        self.assertEqual(self._counts(harness.configuration), (1, 1, 0))
        integrated._ExecutionProbe().assert_no_execution_surfaces(self)
        harness.suspend()
        self._assert_classification(harness.configuration, result.admission, "intent")

    def test_O21_exact_new_admission_retry(self):
        store = self._provision()
        first = self._admit(store)
        self._assert_outcome(first, "newly_admitted")
        before = _snapshot(self.configuration.database_path)
        watermark = store.watermark()
        self.clock.value = RuntimeError("exact history must not sample time")
        second = self._admit(store)
        self._assert_outcome(second, "existing_exact_admission")
        self.assertEqual(second.admission, first.admission)
        self.assertEqual(self.clock.calls, 1)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O22_crash_before_admission_insertion(self):
        self._admission_crash("before_admission_insert")

    def test_O23_crash_after_admission_before_intent(self):
        self._admission_crash("after_admission_insert_before_intent")

    def test_O24_crash_after_intent_before_watermark_commit(self):
        self._admission_crash("after_intent_insert_before_watermark")

    def test_O25_crash_after_watermark_before_commit(self):
        self._admission_crash("after_watermark_before_commit")

    def test_O26_committed_admission_response_loss(self):
        store = self._provision(store_type=fixture.FaultingStore, fault_point="after_commit_before_response")
        self._assert_outcome(self._admit(store), "commit_unknown")
        self.assertEqual(self._counts(), (1, 1, 0))
        before = _snapshot(self.configuration.database_path)
        self.clock.value = RuntimeError("response recovery must not sample again")
        result = self._admit(store)
        self._assert_outcome(result, "existing_exact_admission")
        self.assertEqual(result.admission.decision_time, "2026-09-23T10:30:00.000000Z")
        self.assertEqual(self.clock.calls, 1)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        hard_configuration = self._configuration("committed-hard-exit")
        self._provision(hard_configuration)
        self._run_child(hard_configuration, "admit", "after_commit_before_response")
        clock = fixture.MutableClock(RuntimeError("committed process retry clock forbidden"))
        recovered = self._admit(self._open(hard_configuration, clock=clock))
        self._assert_outcome(recovered, "existing_exact_admission")
        self.assertEqual(clock.calls, 0)
        self.assertEqual(self._counts(hard_configuration), (1, 1, 0))

    def test_O27_uncommitted_admission_response_ambiguity(self):
        store = self._provision()
        original_commit = subject._commit
        with patch.object(subject, "_commit", side_effect=subject._CommitUnknown("synthetic lost commit attempt before durability")):
            self._assert_outcome(self._admit(store), "commit_unknown")
        self.assertIs(subject._commit, original_commit)
        self.assertEqual(self._counts(), (0, 0, 0))
        self.assertEqual(store.watermark(), (None, None))
        self.clock.value = datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc)
        self._assert_outcome(self._admit(store), "expired")
        self.assertEqual(self._counts(), (0, 0, 0))
        self.assertEqual(self.clock.calls, 2)

    def test_O28_sqlite_wal_reopen(self):
        records = _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        first = self._admit(self._open())
        self._assert_outcome(first, "newly_admitted")
        before = _snapshot(self.configuration.database_path)
        with closing(_connect(self.configuration.database_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        reopened = self._open(clock=fixture.MutableClock(RuntimeError("reopen history clock forbidden")))
        self._assert_outcome(self._admit(reopened), "existing_exact_admission")
        for admission in records:
            result = reopened.admit_or_return_existing(_request(self.configuration, admission.grant, admission.tool_binding))
            self._assert_outcome(result, "existing_exact_admission")
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self.assertEqual(self._counts(), (3, 1, 2))

    def test_O29_storage_process_restart(self):
        store = self._provision()
        first = self._admit(store)
        self._assert_outcome(first, "newly_admitted")
        before = _snapshot(self.configuration.database_path)
        output = self._run_child(self.configuration, "restart", "none", expected_exit=0)
        self.assertEqual(json.loads(output), {"outcome": "existing_exact_admission", "intents": 1, "clock_calls": 0})
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O30_legacy_admission_exact_retry(self):
        records = _make_v1(self.configuration)
        _seed_v1_revocation(self.configuration, records[0].grant)
        self._assert_outcome(self._migrate(), "migrated")
        clock = fixture.MutableClock(RuntimeError("legacy retry must not sample time"))
        store = self._open(clock=clock)
        before = _snapshot(self.configuration.database_path)
        for admission in records:
            result = store.admit_or_return_existing(_request(self.configuration, admission.grant, admission.tool_binding))
            self._assert_outcome(result, "existing_exact_admission")
            self.assertEqual(result.admission, admission)
            self._assert_classification(self.configuration, admission, "legacy")
        self.assertEqual(clock.calls, 0)
        self.assertEqual(self._counts(), (2, 0, 2))
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def _assert_classification_audit_rejects(self, configuration, *, message=None):
        with closing(_connect(configuration.database_path)) as connection:
            self.assertEqual(subject._schema_fingerprint(connection), subject._EXPECTED_SCHEMA_FINGERPRINTS[subject.SCHEMA_VERSION])
            keys = {tuple(row) for row in connection.execute(f"SELECT authorization_domain_id,issuer_kind,issuer_id,grant_id FROM {ADMISSIONS}")}
            if message:
                with self.assertRaisesRegex(subject.SqliteAdmissionStoreIntegrityError, message):
                    subject.SqliteAgentExecutionDispatchAdmissionStore._verify_dispatch_classifications(connection, keys)
            else:
                with self.assertRaises(subject.SqliteAdmissionStoreIntegrityError):
                    subject.SqliteAgentExecutionDispatchAdmissionStore._verify_dispatch_classifications(connection, keys)
        self._reject_open(configuration)

    def test_O31_missing_classification(self):
        store = self._provision()
        self._assert_outcome(self._admit(store), "newly_admitted")
        self._corrupt(self.configuration, lambda c: c.execute(f"DELETE FROM {INTENTS}"))
        before = _snapshot(self.configuration.database_path)
        self._assert_classification_audit_rejects(self.configuration, message="exactly one")
        self._assert_outcome(self._admit(store), "integrity_failure")
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O32_intent_marker_overlap(self):
        records = _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        legacy_key = subject._grant_identity(records[0].grant)
        with closing(_connect(self.configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(f"INSERT INTO {INTENTS} VALUES (?, ?, ?, ?)", legacy_key)
        store = self._open()
        self._assert_outcome(self._admit(store), "newly_admitted")
        new_key = subject._grant_identity(self.grant)
        with closing(_connect(self.configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(f"INSERT INTO {MARKERS} VALUES (?, ?, ?, ?, 2)", new_key)
        self._corrupt(self.configuration, lambda c: c.execute(f"INSERT INTO {MARKERS} VALUES (?, ?, ?, ?, 2)", new_key))
        self._assert_classification_audit_rejects(self.configuration, message="exactly one")

    def test_O33_orphan_intent(self):
        self._provision()
        key = subject._grant_identity(self.grant)
        with closing(_connect(self.configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(f"INSERT INTO {INTENTS} VALUES (?, ?, ?, ?)", key)
        self._corrupt(self.configuration, lambda c: c.execute(f"INSERT INTO {INTENTS} VALUES (?, ?, ?, ?)", key))
        self._assert_classification_audit_rejects(self.configuration, message="orphaned")

    def test_O34_orphan_marker(self):
        records = _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        key = subject._grant_identity(records[0].grant)
        with closing(_connect(self.configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(f"DELETE FROM {ADMISSIONS} WHERE grant_id=?", (key[3],))
        self._corrupt(self.configuration, lambda c: c.execute(f"DELETE FROM {ADMISSIONS} WHERE grant_id=?", (key[3],)))
        self._assert_classification_audit_rejects(self.configuration, message="orphaned")
        configuration = self._configuration("orphan-marker-history")
        _make_v1(configuration)
        self._assert_outcome(self._migrate(configuration), "migrated")
        with closing(_connect(configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM admission_schema_migrations WHERE migration_id=2")
        self._corrupt(configuration, lambda c: c.execute(f"UPDATE {MARKERS} SET migration_id=99"))
        self._assert_classification_audit_rejects(configuration, message="migration 2")

        # Separate genuine FK paths from the unconditional immutability guards.
        parent_configuration = self._configuration("marker-parent-fk")
        self._provision(parent_configuration)
        intact = _snapshot(parent_configuration.database_path)
        with closing(_connect(parent_configuration.database_path)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DROP TRIGGER legacy_admission_markers_migration_insert")
            try:
                with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
                    connection.execute(f"INSERT INTO {MARKERS} VALUES (?, ?, ?, ?, 2)", subject._grant_identity(self.grant))
            finally:
                connection.execute("ROLLBACK")
        self.assertEqual(_snapshot(parent_configuration.database_path), intact)
        history_configuration = self._configuration("marker-deferred-history-fk")
        self._provision(history_configuration)
        intact = _snapshot(history_configuration.database_path)
        with closing(_connect(history_configuration.database_path)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DROP TRIGGER legacy_admission_markers_migration_insert")
            connection.execute("DROP TRIGGER admission_schema_migrations_no_delete")
            try:
                connection.execute("DELETE FROM admission_schema_migrations WHERE migration_id=2")
                _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME)
                admission = AgentExecutionDispatchAdmission(self.grant, self.binding, text)
                connection.execute(f"INSERT INTO {ADMISSIONS} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*subject._grant_identity(self.grant), self.grant.run.run_id, subject._encode_grant(self.grant),
                     subject._encode_binding(self.binding), subject._encode_admission(admission), text, key))
                connection.execute(f"INSERT INTO {MARKERS} VALUES (?, ?, ?, ?, 2)", subject._grant_identity(self.grant))
                self.assertIsNotNone(connection.execute("PRAGMA foreign_key_check").fetchone())
                with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
                    connection.execute("COMMIT")
            finally:
                connection.execute("ROLLBACK")
        self.assertEqual(_snapshot(history_configuration.database_path), intact)
        self._open(parent_configuration)
        self._open(history_configuration)

    def test_O35_duplicate_intent_marker_and_replace(self):
        records = _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        self._assert_outcome(self._admit(self._open()), "newly_admitted")
        before = _snapshot(self.configuration.database_path)
        for table, key in ((INTENTS, subject._grant_identity(self.grant)), (MARKERS, (*subject._grant_identity(records[0].grant), 2))):
            for insert in ("INSERT", "INSERT OR REPLACE"):
                with self.subTest(table=table, insert=insert), closing(_connect(self.configuration.database_path)) as connection:
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(f"{insert} INTO {table} VALUES ({','.join('?' for _ in key)})", key)
            # PK/WITHOUT ROWID makes physical duplicates impossible through SQL.
            # Inject a duplicated fetched snapshot row at the real audit seam.
            class DuplicateCursor:
                def __init__(self, cursor):
                    self.cursor = cursor
                def fetchall(self):
                    values = self.cursor.fetchall()
                    return values + values[:1]
            class DuplicateConnection(sqlite3.Connection):
                def execute(self, query, parameters=()):
                    cursor = super().execute(query, parameters)
                    return DuplicateCursor(cursor) if query == f"SELECT * FROM {table}" else cursor
            class SnapshotFaultStore(subject.SqliteAgentExecutionDispatchAdmissionStore):
                @staticmethod
                def _connect_rw(configuration):
                    connection = sqlite3.connect(configuration.database_path.as_uri() + "?mode=rw", uri=True,
                                                 isolation_level=None, factory=DuplicateConnection)
                    connection.row_factory = sqlite3.Row
                    return connection
            with self.subTest(table=table, branch="duplicate-snapshot"):
                with closing(_connect(self.configuration.database_path)) as connection:
                    self.assertEqual(subject._schema_fingerprint(connection), subject._EXPECTED_SCHEMA_FINGERPRINTS[subject.SCHEMA_VERSION])
                with self.assertRaisesRegex(subject.SqliteAdmissionStoreIntegrityError, "duplicated"):
                    self._open(store_type=SnapshotFaultStore)
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O36_wrong_admission_identity_or_parent(self):
        mutations = {
            "indexed-grant": lambda c: (c.execute(f"UPDATE {ADMISSIONS} SET grant_id='wrong-grant'"), c.execute(f"UPDATE {INTENTS} SET grant_id='wrong-grant'")),
            "indexed-issuer": lambda c: (c.execute(f"UPDATE {ADMISSIONS} SET issuer_id='wrong-issuer'"), c.execute(f"UPDATE {INTENTS} SET issuer_id='wrong-issuer'")),
            "intent-wrong-parent": lambda c: c.execute(f"UPDATE {INTENTS} SET grant_id='wrong-parent'"),
            "empty-intent-key": lambda c: c.execute(f"UPDATE {INTENTS} SET grant_id=''"),
            "malformed-issuer-kind": lambda c: c.execute(f"UPDATE {INTENTS} SET issuer_kind='unknown'"),
        }
        for name, mutation in mutations.items():
            with self.subTest(branch=name):
                configuration = self._configuration("identity-" + name)
                store = self._provision(configuration)
                self._assert_outcome(self._admit(store), "newly_admitted")
                self._corrupt(configuration, mutation)
                before = _snapshot(configuration.database_path)
                self._reject_open(configuration)
                self._assert_outcome(self._admit(store), "integrity_failure")
                self.assertEqual(_snapshot(configuration.database_path), before)

    def test_O37_run_relationship_mismatch(self):
        for branch in ("index", "grant", "binding", "admission-grant", "admission-binding",
                       "grant-contract", "binding-contract", "admission-grant-contract", "admission-binding-contract"):
            with self.subTest(branch=branch):
                configuration = self._configuration("run-" + branch)
                store = self._provision(configuration)
                self._assert_outcome(self._admit(store), "newly_admitted")
                def mutate(connection):
                    if branch == "index":
                        connection.execute(f"UPDATE {ADMISSIONS} SET run_id='wrong-run'")
                        return
                    column = "grant_json" if branch.startswith("grant") else ("binding_json" if branch.startswith("binding") else "admission_json")
                    document = json.loads(connection.execute(f"SELECT {column} FROM {ADMISSIONS}").fetchone()[0])
                    if branch.startswith("admission-"):
                        document = dict(document)
                        nested = "grant" if branch.startswith("admission-grant") else "tool_binding"
                        run_document = document[nested]["run"]
                    else:
                        run_document = document["run"]
                    if branch.endswith("contract"):
                        run_document["contract"]["resource"] = "synthetic/contradictory-resource.txt"
                    else:
                        run_document["run_id"] = "wrong-run"
                    connection.execute(f"UPDATE {ADMISSIONS} SET {column}=?", (subject._canonical_json(document),))
                self._corrupt(configuration, mutate)
                with closing(_connect(configuration.database_path)) as connection:
                    self.assertEqual(subject._schema_fingerprint(connection), subject._EXPECTED_SCHEMA_FINGERPRINTS[subject.SCHEMA_VERSION])
                self._reject_open(configuration)
                self._assert_outcome(self._admit(store), "integrity_failure")

    def test_O38_grant_composite_conflict_precedence(self):
        store = self._provision()
        self._assert_outcome(self._admit(store), "newly_admitted")
        cases = ((replace(self.grant, provenance_reference="rebound-approval"), self.binding, "grant_identity_conflict"),
                 (self.grant, replace(self.binding, tool_id="tool::different"), "binding_conflict"),
                 (replace(self.grant, grant_id="grant::another"), self.binding, "run_conflict"))
        for grant, binding, outcome in cases:
            with self.subTest(outcome=outcome):
                self._assert_outcome(self._admit(store, grant=grant, binding=binding), outcome)
                self.assertEqual(self._counts(), (1, 1, 0))
        other_run = fixture.make_run("run::composite-namespace")
        other = fixture.make_grant(bound_run=other_run, issuer_id="issuer::different")
        self._assert_outcome(self._admit(store, grant=other, binding=fixture.make_binding(bound_run=other_run)), "newly_admitted")
        self.assertEqual(self._counts(), (2, 2, 0))

    def test_O39_domain_ledger_instance_generation_mismatch(self):
        self._provision()
        before = _snapshot(self.configuration.database_path)
        for branch, changed in (("domain", replace(self.configuration, authorization_domain_id="domain::wrong")),
                                ("instance", replace(self.configuration, ledger_instance_id="ledger::wrong")),
                                ("generation", replace(self.configuration, domain_generation=2))):
            with self.subTest(branch=branch):
                self._reject_open(changed)
                result = subject.SqliteAgentExecutionDispatchAdmissionStore.migrate(changed, access=fixture.administration_access(changed))
                self._assert_outcome(result, "integrity_failure")
                self.assertEqual(_snapshot(self.configuration.database_path), before)
        wrong_grant = replace(self.grant, authorization_domain_id="domain::wrong")
        self._assert_outcome(self._admit(self._open(), grant=wrong_grant), "domain_mismatch")
        self.assertEqual(self._counts(), (0, 0, 0))

    def test_O40_immutable_update_delete_rebind(self):
        _make_v1(self.configuration)
        self._assert_outcome(self._migrate(), "migrated")
        self._assert_outcome(self._admit(self._open()), "newly_admitted")
        before = _snapshot(self.configuration.database_path)
        for table in (INTENTS, MARKERS):
            mutations = (f"UPDATE {table} SET issuer_id=issuer_id", f"DELETE FROM {table}",
                         f"UPDATE {table} SET grant_id='rebound'")
            if table == MARKERS:
                mutations += (f"UPDATE {table} SET migration_id=1",)
            for mutation in mutations:
                with self.subTest(table=table, mutation=mutation), closing(_connect(self.configuration.database_path)) as connection:
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(mutation)
        for mutation in (f"UPDATE {ADMISSIONS} SET run_id='rebound'", f"DELETE FROM {ADMISSIONS}"):
            with self.subTest(parent=mutation), closing(_connect(self.configuration.database_path)) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(mutation)
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_O41_positive_equal_and_regressing_watermark(self):
        store = self._provision()
        first = self._admit(store)
        self._assert_outcome(first, "newly_admitted")
        self.assertEqual(self.clock.calls, 1)
        watermark = store.watermark()
        run = fixture.make_run("run::equal-watermark")
        grant = fixture.make_grant(bound_run=run, grant_id="grant::equal-watermark")
        self._assert_outcome(self._admit(store, grant=grant, binding=fixture.make_binding(bound_run=run)), "newly_admitted")
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self.clock.calls, 2)
        self.clock.value = fixture.DECISION_TIME - timedelta(microseconds=1)
        run = fixture.make_run("run::regressing-watermark")
        grant = fixture.make_grant(bound_run=run, grant_id="grant::regressing-watermark")
        self._assert_outcome(self._admit(store, grant=grant, binding=fixture.make_binding(bound_run=run)), "clock_regression")
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._counts(), (2, 2, 0))

    def test_O42_temporal_revocation_denial_watermark(self):
        for branch, now in (("not_yet_current", datetime(2026, 9, 23, 9, 59, 59, tzinfo=timezone.utc)),
                            ("expired", datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc)),
                            ("revoked", fixture.DECISION_TIME + timedelta(minutes=1))):
            with self.subTest(branch=branch):
                configuration = self._configuration("denial-" + branch)
                clock = fixture.MutableClock(fixture.DECISION_TIME if branch == "revoked" else now)
                store = self._provision(configuration, clock=clock)
                if branch == "revoked":
                    self._assert_outcome(store.revoke_or_return_existing(_mint_revocation_request(configuration.authorization_domain_id, self.grant)), "newly_revoked")
                    clock.value = now
                self._assert_outcome(self._admit(store), branch)
                self.assertEqual(store.watermark()[0], subject._canonical_decision_time(now)[1])
                self.assertEqual(self._counts(configuration), (0, 0, 0))

    def test_O43_retry_migration_watermark_invariance(self):
        records = _make_v1(self.configuration)
        with closing(_connect(self.configuration.database_path)) as connection:
            watermark = tuple(connection.execute("SELECT last_decision_time,last_decision_time_key FROM admission_ledger_metadata").fetchone())
        self._assert_outcome(self._migrate(), "migrated")
        store = self._open(clock=fixture.MutableClock(RuntimeError("legacy/migration clock forbidden")))
        self.assertEqual(store.watermark(), watermark)
        before = _snapshot(self.configuration.database_path)
        for admission in records:
            result = store.admit_or_return_existing(_request(self.configuration, admission.grant, admission.tool_binding))
            self._assert_outcome(result, "existing_exact_admission")
            self.assertEqual(result.admission.decision_time, admission.decision_time)
        self._assert_outcome(self._migrate(), "already_current")
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self.assertEqual(store._clock.calls, 0)

    def test_O44_revocation_ordering_and_immutable_history(self):
        before_configuration = self._configuration("revocation-first")
        before_store = self._provision(before_configuration)
        self._assert_outcome(before_store.revoke_or_return_existing(_mint_revocation_request(before_configuration.authorization_domain_id, self.grant)), "newly_revoked")
        self._assert_outcome(self._admit(before_store), "revoked")
        self.assertEqual(self._counts(before_configuration), (0, 0, 0))
        store = self._provision()
        first = self._admit(store)
        self._assert_outcome(first, "newly_admitted")
        self._assert_outcome(store.revoke_or_return_existing(_mint_revocation_request(self.configuration.authorization_domain_id, self.grant)), "newly_revoked")
        self.clock.value = RuntimeError("revoked historical retry cannot sample clock")
        second = self._admit(store)
        self._assert_outcome(second, "existing_exact_admission")
        self.assertEqual(second.admission, first.admission)
        self._assert_classification(self.configuration, first.admission, "intent")
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O45_concurrent_identical_admission_writers(self):
        store = self._provision()
        start = threading.Barrier(2, timeout=10)
        outcomes = []
        errors = []
        def admit():
            try:
                start.wait()
                outcomes.append(self._admit(store).outcome.value)
            except BaseException as error:
                errors.append(error)
        threads = [threading.Thread(target=admit, daemon=True) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(15)
        self.assertFalse(any(thread.is_alive() for thread in threads), "owned storage thread did not finish")
        self.assertEqual(errors, [])
        self.assertEqual(sorted(outcomes), ["existing_exact_admission", "newly_admitted"])
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O46_busy_storage_clock_and_regression_fail_closed(self):
        configuration = replace(self.configuration, busy_timeout_ms=50)
        store = self._provision(configuration)
        with closing(_connect(configuration.database_path)) as blocker:
            blocker.execute("BEGIN IMMEDIATE")
            self._assert_outcome(self._admit(store), "storage_busy")
            blocker.execute("ROLLBACK")
        self.assertEqual(self._counts(configuration), (0, 0, 0))
        self.assertEqual(store.watermark(), (None, None))
        renamed = self.root / "unavailable-closed.sqlite3"
        configuration.database_path.rename(renamed)
        try:
            self._assert_outcome(self._admit(store), "storage_unavailable")
            self.assertFalse(configuration.database_path.exists())
        finally:
            renamed.rename(configuration.database_path)
        bad_clocks = (("raised-exception", RuntimeError("clock threw")), ("wrong-type", object()),
                      ("naive", datetime(2026, 9, 23, 10, 30)),
                      ("non-UTC", datetime(2026, 9, 23, 12, 30, tzinfo=timezone(timedelta(hours=2)))))
        for label, value in bad_clocks:
            with self.subTest(clock=label):
                self.clock.value = value
                self._assert_outcome(self._admit(store), "clock_failure")
                self.assertEqual(self._counts(configuration), (0, 0, 0))
                self.assertEqual(store.watermark(), (None, None))
        self.clock.value = fixture.DECISION_TIME
        self._assert_outcome(self._admit(store), "newly_admitted")
        watermark = store.watermark()
        run = fixture.make_run("run::clock-after-consumption")
        grant = fixture.make_grant(bound_run=run, grant_id="grant::clock-after-consumption")
        self.clock.value = fixture.DECISION_TIME - timedelta(seconds=1)
        self._assert_outcome(self._admit(store, grant=grant, binding=fixture.make_binding(bound_run=run)), "clock_regression")
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._counts(configuration), (1, 1, 0))

    def test_O55_packaged_migration_resources_and_declarations(self):
        import ast
        import tomllib
        declaration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        surfaces = declaration["tool"]["setuptools"]["packages"]
        self.assertIn("engineering_orchestration", surfaces)
        self.assertIn(subject.MIGRATION_PACKAGE, surfaces)
        self.assertFalse(any("experiment" in name for name in surfaces))
        self.assertEqual(declaration["tool"]["setuptools"]["package-data"][subject.MIGRATION_PACKAGE], ["*.sql"])
        migrations = subject._migration_bytes()
        self.assertEqual([(item[0], item[1]) for item in migrations], [(1, "0001_initial.sql"), (2, "0002_dispatch_outbox.sql"), (3, "0003_dispatch_claim_lease.sql")])
        self.assertEqual(migrations[0][2], V1_CHECKSUM)
        for _, _, checksum, data in migrations:
            self.assertEqual(hashlib.sha256(data).hexdigest(), checksum)
            self.assertNotIn(b"\r", data)
        self._provision()
        with closing(_connect(self.configuration.database_path)) as connection:
            self.assertEqual(subject._schema_fingerprint(connection), subject._EXPECTED_SCHEMA_FINGERPRINTS[subject.SCHEMA_VERSION])
            self.assertEqual([tuple(row) for row in connection.execute("SELECT * FROM admission_schema_migrations ORDER BY migration_id")],
                             [(number, name, checksum) for number, name, checksum, _ in migrations])
        v1_configuration = self._configuration("packaged-v1-fingerprint")
        _make_v1(v1_configuration, nonempty=False)
        with closing(_connect(v1_configuration.database_path)) as connection:
            self.assertEqual(subject._schema_fingerprint(connection), V1_FINGERPRINT)
        for exact_path in ("engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py",
                           "engineering_orchestration/_sqlite_admission_migrations/__init__.py"):
            tree = ast.parse((ROOT / exact_path).read_text(encoding="utf-8"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
            self.assertFalse(any(name.startswith("experiments") for name in imports))
        # Actual built-archive inspection is independent mandatory P1 evidence.
        # These declaration/runtime-resource checks do not substitute for it.

    def test_O56_validation_target_process_and_cleanup_safety(self):
        self.assertEqual(self.root.parent, self.parent)
        self.assertEqual((self.root / ".aio055-owner").read_text(encoding="ascii"), self.nonce)
        self.assertFalse(self.configuration.database_path.exists())
        self._run_child(self.configuration, "timeout", "none", timeout=0.5, expected_exit=0)
        self.assertFalse(self.configuration.database_path.exists())
        self.assertGreater(len(_PROCESS_EVIDENCE), 0)
        for record in _PROCESS_EVIDENCE:
            with self.subTest(mode=record["mode"], root=Path(record["root"]).name):
                self.assertTrue(record["reaped"])
                self.assertTrue(record["pipes_closed"])
                self.assertFalse(record["shell"])
                self.assertLessEqual(set(record["environment"]), {"SystemRoot", "WINDIR", "TEMP", "TMP"})
                self.assertEqual(Path(record["root"]).parent, self.parent)
                if Path(record["root"]) != self.root:
                    self.assertFalse(Path(record["root"]).exists(), "prior exact owned probe root leaked")
        self.assertTrue(_PROCESS_EVIDENCE[-1]["timeout"], "finite-timeout cleanup branch was not exercised")
        child_root = self.root / "cleanup-example"
        child_root.mkdir()
        (child_root / ".aio055-owner").write_text(self.nonce, encoding="ascii")
        self.assertEqual(child_root.resolve().parent, self.root)
        self.assertEqual((child_root / ".aio055-owner").read_text(encoding="ascii"), self.nonce)
        shutil.rmtree(child_root)
        self.assertFalse(child_root.exists())

    def test_O57_operational_legacy_marker_creation_rejected(self):
        store = self._provision()
        before = _snapshot(self.configuration.database_path)
        with closing(_connect(self.configuration.database_path)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME)
                admission = AgentExecutionDispatchAdmission(self.grant, self.binding, text)
                connection.execute(f"INSERT INTO {ADMISSIONS} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*subject._grant_identity(self.grant), self.grant.run.run_id, subject._encode_grant(self.grant),
                     subject._encode_binding(self.binding), subject._encode_admission(admission), text, key))
                with self.assertRaisesRegex(sqlite3.IntegrityError, "dirty v1 migration"):
                    connection.execute(f"INSERT INTO {MARKERS} VALUES (?, ?, ?, ?, 2)", subject._grant_identity(self.grant))
            finally:
                connection.execute("ROLLBACK")
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        for flag in ("legacy", "dispatch_enabled", "classification"):
            with self.subTest(caller_flag=flag):
                result = store.admit_or_return_existing({"grant": self.grant, "tool_binding": self.binding, flag: True})
                self._assert_outcome(result, "invalid_input")
                self.assertEqual(self._counts(), (0, 0, 0))
        self._assert_outcome(self._admit(store), "newly_admitted")
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O58_corrupt_source_payload_revocation_watermark(self):
        def bad_json(connection):
            connection.execute(f"UPDATE {ADMISSIONS} SET admission_json='not-json'")
        def mismatched_payload(connection):
            connection.execute(f"UPDATE {ADMISSIONS} SET run_id='wrong-run' WHERE grant_id='grant::aio055-legacy-0'")
        def malformed_revocation(connection):
            connection.execute("UPDATE agent_execution_grant_revocations SET grant_json='not-json'")
        def rebound_revocation(connection):
            value = json.loads(connection.execute("SELECT grant_json FROM agent_execution_grant_revocations").fetchone()[0])
            value["provenance_reference"] = "rebound"
            connection.execute("UPDATE agent_execution_grant_revocations SET grant_json=?", (subject._canonical_json(value),))
        def early_revocation(connection):
            _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME - timedelta(minutes=1))
            connection.execute("UPDATE agent_execution_grant_revocations SET revocation_time=?,revocation_time_key=?", (text, key))
        def regressing_watermark(connection):
            _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME - timedelta(minutes=1))
            connection.execute("UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?", (text, key))
        mutations = {
            "payload-malformed": bad_json,
            "payload-index-mismatch": mismatched_payload,
            "revocation-malformed": malformed_revocation,
            "revocation-rebound": rebound_revocation,
            "revocation-precedes-admission": early_revocation,
            "watermark-malformed": lambda c: c.execute("UPDATE admission_ledger_metadata SET last_decision_time='not-time'"),
            "watermark-key-mismatch": lambda c: c.execute("UPDATE admission_ledger_metadata SET last_decision_time_key=last_decision_time_key+1"),
            "watermark-missing": lambda c: c.execute("UPDATE admission_ledger_metadata SET last_decision_time=NULL,last_decision_time_key=NULL"),
            "watermark-regression": regressing_watermark,
            "source-foreign-key": lambda c: c.execute(f"UPDATE {ADMISSIONS} SET authorization_domain_id='foreign-domain'"),
            "revocation-state-incomplete": lambda c: c.execute("UPDATE admission_ledger_metadata SET revocation_state_complete=0"),
            "source-fenced": lambda c: c.execute("UPDATE admission_ledger_metadata SET activation_state='fenced'"),
        }
        for branch, mutation in mutations.items():
            with self.subTest(branch=branch):
                configuration = self._configuration("source-corrupt-" + branch)
                records = _make_v1(configuration)
                revoked = records[0].grant
                _, text, key = subject._canonical_decision_time(fixture.DECISION_TIME + timedelta(minutes=1))
                with closing(_connect(configuration.database_path)) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("INSERT INTO agent_execution_grant_revocations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (*subject._grant_identity(revoked), revoked.run.run_id, subject._encode_grant(revoked),
                         revoked.issuer_kind, revoked.issuer_id, text, key))
                    connection.execute("UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?", (text, key))
                    connection.execute("COMMIT")
                self._corrupt(configuration, mutation)
                with closing(_connect(configuration.database_path)) as connection:
                    self.assertEqual(subject._schema_fingerprint(connection), V1_FINGERPRINT)
                before = _snapshot(configuration.database_path)
                self._assert_outcome(self._migrate(configuration), "incompatible_schema" if branch == "source-fenced" else "integrity_failure")
                self.assertEqual(_snapshot(configuration.database_path), before)
                self.assertEqual(before[2], 1)
                self.assertNotIn(INTENTS, dict(before[1]))
                self.assertNotIn(MARKERS, dict(before[1]))

    def test_O59_missing_marker_before_migration_commit(self):
        _make_v1(self.configuration)
        before = _snapshot(self.configuration.database_path)
        observed = []
        class OmittingBackfillConnection(sqlite3.Connection):
            def execute(self, query, parameters=()):
                if query.startswith("INSERT INTO legacy_admission_markers"):
                    query = query.rstrip().rstrip(";") + " WHERE grant_id <> (SELECT MIN(grant_id) FROM agent_execution_dispatch_admissions);"
                    cursor = super().execute(query, parameters)
                    observed.append(super().execute(f"SELECT count(*) FROM {MARKERS}").fetchone()[0])
                    return cursor
                return super().execute(query, parameters)
        class MissingMarkerStore(subject.SqliteAgentExecutionDispatchAdmissionStore):
            @staticmethod
            def _connect_rw(configuration):
                connection = sqlite3.connect(configuration.database_path.as_uri() + "?mode=rw", uri=True,
                    isolation_level=None, factory=OmittingBackfillConnection)
                connection.row_factory = sqlite3.Row
                return connection
        result = self._migrate(store_type=MissingMarkerStore)
        self._assert_outcome(result, "integrity_failure")
        self.assertIn("exactly one", result.detail)
        self.assertEqual(observed, [1])
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self._assert_outcome(self._migrate(), "migrated")
        self.assertEqual(self._counts(), (2, 0, 2))

    def test_O47_no_claim_lease_api(self):
        store = self._provision()
        admitted = self._admit(store)
        self._assert_outcome(admitted, "newly_admitted")
        forbidden = (
            "claim", "claim_intent", "renew", "renew_lease", "reclaim",
            "assess_current_claim", "select_worker", "dispatch_loop",
            "enumerate_intents", "list_intents", "select_eligible_intent",
        )
        for target in (store, subject.SqliteAgentExecutionDispatchAdmissionStore,
                       integrated.LocalOperationalTrustCoordinator):
            for name in forbidden:
                with self.subTest(target=type(target).__name__, name=name):
                    self.assertFalse(hasattr(target, name))
        with closing(_connect(self.configuration.database_path)) as connection:
            columns = {
                table: tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))
                for table in (INTENTS, MARKERS)
            }
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        self.assertEqual(columns[INTENTS], ("authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"))
        self.assertEqual(columns[MARKERS], columns[INTENTS] + ("migration_id",))
        for name in ("dispatch_claims", "lease_renewals", "dispatch_workers"):
            self.assertNotIn(name, tables)
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_O48_no_invocation_result_path(self):
        harness = integrated._WindowsHarness(self)
        coordinator = harness.coordinator
        self.assertIsNotNone(coordinator)
        run = integrated._make_run("run::aio055-no-invocation")
        principal, proof = harness.human_authority(run)
        probe = integrated._ExecutionProbe()
        original_open = Path.open
        resource_calls = []
        def guard_resource(path, *args, **kwargs):
            lexical = str(path).replace(chr(92), "/")
            if lexical == run.contract.resource or lexical.endswith("/" + run.contract.resource):
                resource_calls.append(lexical)
                raise AssertionError("abstract operation resource must never be opened")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", new=guard_resource), patch.object(
                subprocess, "Popen", side_effect=AssertionError("no production dispatch process")) as spawn:
            result = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
            self._assert_outcome(result, "newly_admitted")
            probe.observe_binding(result.admission.tool_binding)
            probe.assert_no_execution_surfaces(self)
            denied_run = integrated._make_run("run::aio055-no-invocation-denied")
            denied_principal, denied_proof = harness.policy_authority(denied_run, decision="deny")
            denied = coordinator.admit(run=denied_run, authenticated_principal=denied_principal, authority_proof=denied_proof)
            self.assertNotIn(denied.outcome.value, {"newly_admitted", "existing_exact_admission"})
            unknown_run = integrated._make_run("run::aio055-no-invocation-route", runtime_option_id="runtime::untrusted")
            unknown_principal, unknown_proof = harness.human_authority(unknown_run)
            unknown = coordinator.admit(run=unknown_run, authenticated_principal=unknown_principal, authority_proof=unknown_proof)
            self._assert_outcome(unknown, "untrusted_tool_binding")
            blocked_run = integrated._make_run("run::aio055-no-invocation-prerequisite")
            blocked_principal, blocked_proof = harness.human_authority(blocked_run)
            harness.fresh_source.failure = RuntimeError("synthetic unavailable prerequisites")
            blocked = coordinator.admit(run=blocked_run, authenticated_principal=blocked_principal, authority_proof=blocked_proof)
            self._assert_outcome(blocked, "unsatisfied_prerequisites")
            harness.fresh_source.failure = None
            self.assertEqual(self._counts(harness.configuration), (1, 1, 0))
        spawn.assert_not_called()
        self.assertEqual(resource_calls, [])
        for target in (coordinator, coordinator._session, result.admission.tool_binding, result.admission):
            for name in ("dispatch", "invoke", "read_resource", "probe_availability",
                         "resolve_credentials", "attach_result", "consume"):
                self.assertFalse(hasattr(target, name), (type(target).__name__, name))
        self.assertEqual(self._counts(harness.configuration), (1, 1, 0))
        harness.suspend()

    def test_O49_public_compatibility(self):
        self.assertEqual(tuple(field.name for field in fields(AgentExecutionDispatchAdmission)),
                         ("grant", "tool_binding", "decision_time"))
        schema = json.loads((ROOT / "schemas/agent-execution-dispatch-admission.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["properties"]), {"grant", "tool_binding", "decision_time"})
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertIs(schema["additionalProperties"], False)
        self.assertFalse((ROOT / "schemas/agent-execution-dispatch-intent.schema.json").exists())
        self.assertFalse(hasattr(package, "AgentExecutionDispatchIntent"))
        self.assertNotIn("_DispatchClassification", getattr(package, "__all__", ()))
        self.assertNotIn("_DispatchClassification", subject.__all__)
        expected_outcomes = {
            "newly_admitted", "existing_exact_admission", "newly_revoked", "existing_exact_revocation",
            "no_existing_admission", "not_yet_current", "expired", "revoked", "domain_mismatch",
            "grant_identity_conflict", "binding_conflict", "run_conflict", "invalid_input",
            "unauthenticated_grant", "untrusted_tool_binding", "unsatisfied_prerequisites",
            "storage_busy", "storage_unavailable", "incompatible_schema", "integrity_failure",
            "clock_failure", "clock_regression", "commit_unknown",
        }
        self.assertEqual({value.value for value in integrated.AgentExecutionDispatchAdmissionStoreOutcome}, expected_outcomes)
        public_store = {name for name in subject.SqliteAgentExecutionDispatchAdmissionStore.__dict__ if not name.startswith("_")}
        self.assertEqual(public_store, {
            "provision", "migrate", "verified_settings", "watermark", "classify_guarded_history",
            "load_authoritative_admission", "admit_or_return_existing", "revoke_or_return_existing",
            "fence", "create_fenced_backup",
        })
        self.assertEqual({value.value for value in integrated.AgentExecutionDispatchAdmissionStoreRetryDisposition}, {
            "no_retry_needed", "do_not_retry_same_request", "retry_exact_request", "retry_at_or_after_issuance",
            "recollect_fresh_state", "retry_after_remediation", "reconcile_administrative_state",
        })

    def test_O50_private_future_seam(self):
        store = self._provision()
        positive = self._admit(store)
        self._assert_outcome(positive, "newly_admitted")
        value = self._assert_classification(self.configuration, positive.admission, "intent")
        self.assertEqual(tuple(field.name for field in fields(type(value))), ("admission", "kind"))
        self.assertFalse(callable(value))
        for field in fields(type(value)):
            self.assertNotIsInstance(getattr(value, field.name), sqlite3.Connection)
        for name in ("connection", "execute", "cursor", "claim", "enumerate", "dispatchable", "authority"):
            self.assertFalse(hasattr(value, name))
        rebound = replace(positive.admission, tool_binding=replace(positive.admission.tool_binding, tool_id="tool::rebound"))
        with closing(store._open_existing(allow_fenced=False)) as connection:
            with self.assertRaises(subject.SqliteAdmissionStoreIntegrityError):
                store._classify_admission_dispatch(connection, rebound)
        legacy_configuration = self._configuration("future-seam-legacy")
        originals = _make_v1(legacy_configuration)
        self._assert_outcome(self._migrate(legacy_configuration), "migrated")
        for original in originals:
            self._assert_classification(legacy_configuration, original, "legacy")
        self.assertEqual(self._counts(legacy_configuration), (2, 0, 2))

    def test_O51_ownership_loss_around_commit(self):
        for branch in ("before-store", "after-commit"):
            with self.subTest(branch=branch):
                harness = integrated._WindowsHarness(self)
                coordinator = harness.coordinator
                session = coordinator._session
                session_type = type(session)
                run = integrated._make_run("run::aio055-loss-" + branch)
                principal, proof = harness.human_authority(run)
                original_revalidate = session_type._revalidate
                original_produce = integrated.LocalOperationalTrustCoordinator._produce
                original_fault = subject.SqliteAgentExecutionDispatchAdmissionStore._fault
                armed = False
                def fail_postcheck(candidate):
                    if candidate is session and armed:
                        raise integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError("synthetic lost ownership")
                    return original_revalidate(candidate)
                def arm_after_production(candidate, **kwargs):
                    nonlocal armed
                    produced = original_produce(candidate, **kwargs)
                    if branch == "before-store":
                        armed = True
                    return produced
                def arm_after_commit(candidate, point):
                    nonlocal armed
                    original_fault(candidate, point)
                    if branch == "after-commit" and point == "after_commit_before_response":
                        armed = True
                with patch.object(session_type, "_revalidate", new=fail_postcheck), patch.object(
                        integrated.LocalOperationalTrustCoordinator, "_produce", new=arm_after_production), patch.object(
                        subject.SqliteAgentExecutionDispatchAdmissionStore, "_fault", new=arm_after_commit):
                    result = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
                self._assert_outcome(result, "integrity_failure")
                self.assertIsNone(result.admission)
                self.assertTrue(armed)
                self.assertEqual(self._counts(harness.configuration), (0, 0, 0) if branch == "before-store" else (1, 1, 0))
                durable = _snapshot(harness.configuration.database_path)
                retry = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
                self.assertNotIn(retry.outcome.value, {"newly_admitted", "existing_exact_admission"})
                self.assertIsNone(getattr(retry, "admission", None))
                self.assertEqual(_snapshot(harness.configuration.database_path), durable)
                self.assertEqual(coordinator._domain_identity.ledger_instance_id, harness.configuration.ledger_instance_id)
                harness.suspend()

    def test_O52_integrated_same_live_session_retry(self):
        harness = integrated._WindowsHarness(self)
        coordinator = harness.coordinator
        run = integrated._make_run("run::aio055-live-presentation")
        principal, proof = harness.human_authority(run)
        produced, presentation = coordinator._produce(run=run, authenticated_principal=principal, authority_proof=proof)
        self.assertEqual(produced.outcome.value, "issued")
        self.assertIsNotNone(presentation)
        first = coordinator._session.admit(presentation)
        self._assert_outcome(first, "newly_admitted")
        self.assertEqual(self._counts(harness.configuration), (1, 1, 0))
        prepared_calls = harness.fresh_source.calls
        durable = _snapshot(harness.configuration.database_path)
        production_retry, same_presentation = coordinator._produce(run=run, authenticated_principal=principal, authority_proof=proof)
        self.assertEqual(production_retry.outcome.value, "existing_exact_issuance")
        self.assertIs(same_presentation, presentation)
        with patch.object(subject.SqliteAgentExecutionDispatchAdmissionStore, "_sample_clock",
                          side_effect=AssertionError("exact Store history may not sample the clock")):
            retry = coordinator._session.admit(same_presentation)
            loaded = coordinator._session.load_authoritative_admission(presentation)
        self._assert_outcome(retry, "existing_exact_admission")
        self._assert_outcome(loaded, "existing_exact_admission")
        self.assertEqual(retry.admission, first.admission)
        self.assertEqual(loaded.admission, first.admission)
        self.assertEqual(harness.fresh_source.calls, prepared_calls)
        self.assertEqual(_snapshot(harness.configuration.database_path), durable)
        harness.suspend()

    def test_O53_integrated_presentation_lost_on_restart(self):
        harness = integrated._WindowsHarness(self)
        coordinator = harness.coordinator
        old_session = coordinator._session
        run = integrated._make_run("run::aio055-before-producer-restart")
        principal, proof = harness.human_authority(run)
        produced, presentation = coordinator._produce(run=run, authenticated_principal=principal, authority_proof=proof)
        self.assertEqual(produced.outcome.value, "issued")
        original = old_session.admit(presentation)
        self._assert_outcome(original, "newly_admitted")
        durable = _snapshot(harness.configuration.database_path)
        prior_grant_sequence = harness.grant_ids._counter
        harness.restart()
        # A new synthetic entropy source must continue the owned fixture sequence.
        harness.grant_ids._counter = prior_grant_sequence
        self.assertIsNot(harness.coordinator, coordinator)
        self.assertIsNot(harness.coordinator._session, old_session)
        rejected = harness.coordinator._session.load_authoritative_admission(presentation)
        self._assert_outcome(rejected, "unauthenticated_grant")
        self.assertIsNone(rejected.admission)
        self.assertEqual(harness.fresh_source.calls, 0)
        self.assertEqual(_snapshot(harness.configuration.database_path), durable)
        fresh_run = integrated._make_run("run::aio055-after-producer-restart")
        fresh_principal, fresh_proof = harness.human_authority(fresh_run)
        fresh = harness.coordinator.admit(run=fresh_run, authenticated_principal=fresh_principal, authority_proof=fresh_proof)
        self._assert_outcome(fresh, "newly_admitted")
        self.assertNotEqual(fresh.admission.grant.run, original.admission.grant.run)
        self.assertNotEqual(fresh.admission.grant.grant_id, original.admission.grant.grant_id)
        self.assertEqual(self._counts(harness.configuration), (2, 2, 0))
        harness.suspend()

    def test_O54_administrative_quiescence(self):
        harness = integrated._WindowsHarness(self)
        admin = integrated.windows_owner.WindowsLocalAuthorizationDomainAdministration(clock=harness.clock, busy_timeout_ms=2000)
        before = _snapshot(harness.configuration.database_path)
        for lease_active in (False, True):
            with self.subTest(lease_active=lease_active):
                if lease_active:
                    with harness.coordinator._session.operation():
                        with self.assertRaises(integrated.windows_owner.AuthorizationDomainAlreadyOwnedError):
                            admin.migrate(harness.domain_id)
                else:
                    with self.assertRaises(integrated.windows_owner.AuthorizationDomainAlreadyOwnedError):
                        admin.migrate(harness.domain_id)
                self.assertEqual(_snapshot(harness.configuration.database_path), before)
        harness.close()
        originals = _make_v1(harness.configuration, reset=True)
        with closing(_connect(harness.configuration.database_path)) as reader, closing(_connect(harness.configuration.database_path)) as writer:
            reader.execute("BEGIN")
            self.assertEqual(reader.execute("PRAGMA user_version").fetchone()[0], 1)
            writer.execute("BEGIN EXCLUSIVE")
            self.assertEqual(reader.execute("PRAGMA user_version").fetchone()[0], 1)
            writer.execute("ROLLBACK")
            reader.execute("ROLLBACK")
        self._assert_outcome(admin.migrate(harness.domain_id), "migrated")
        self.assertEqual(self._counts(harness.configuration), (len(originals), 0, len(originals)))
        harness._install_adapters_and_compose()
        self.assertEqual(harness.coordinator._domain_identity.domain_generation, harness.configuration.domain_generation)
        harness.suspend()

    def test_O60_fresh_prerequisite_binding_and_description_rejection(self):
        harness = integrated._WindowsHarness(self)
        coordinator = harness.coordinator
        for branch in ("missing", "invalid", "unavailable", "unsatisfied", "wrong-subject", "invalid-mode"):
            with self.subTest(fresh_branch=branch):
                run = integrated._make_run("run::aio055-fresh-block-" + branch)
                principal, proof = harness.human_authority(run)
                source = harness.fresh_source
                source.use_override = branch != "unavailable"
                source.failure = RuntimeError("synthetic fresh source failure") if branch == "unavailable" else None
                source.override = {
                    "missing": None, "invalid": object(), "unavailable": None,
                    "unsatisfied": integrated._make_unsatisfied_parent_inputs(run),
                    "wrong-subject": integrated._make_parent_inputs(integrated._make_run("run::aio055-other-subject", resource="synthetic/aio055-other-subject.txt")),
                    "invalid-mode": integrated._make_parent_inputs(run),
                }[branch]
                harness.mode_resolver.mode = "invalid-mode" if branch == "invalid-mode" else integrated.EXECUTION_MODE
                result = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
                self._assert_outcome(result, "unsatisfied_prerequisites")
                self.assertIsNone(result.admission)
                self.assertEqual(self._counts(harness.configuration), (0, 0, 0))
                source.failure = None
        harness.fresh_source.use_override = False
        harness.mode_resolver.mode = integrated.EXECUTION_MODE
        binding_cases = (
            ("missing", None, "untrusted_tool_binding"),
            ("malformed", object(), "invalid_input"),
            ("wrong-run", integrated.AgentOperationToolBinding(integrated._make_run("run::aio055-wrong-binding"), integrated.TOOL_ID), "invalid_input"),
        )
        for branch, binding, expected in binding_cases:
            with self.subTest(binding_branch=branch):
                run = integrated._make_run("run::aio055-binding-block-" + branch)
                principal, proof = harness.human_authority(run)
                calls = harness.fresh_source.calls
                with patch.object(integrated.TrustedAgentOperationToolBindingResolver, "resolve_tool_binding", return_value=binding):
                    result = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
                self._assert_outcome(result, expected)
                self.assertIsNone(result.admission)
                self.assertEqual(harness.fresh_source.calls, calls)
                self.assertEqual(self._counts(harness.configuration), (0, 0, 0))
        run = integrated._make_run("run::aio055-untrusted-route", runtime_option_id="runtime::untrusted")
        principal, proof = harness.human_authority(run)
        result = coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
        self._assert_outcome(result, "untrusted_tool_binding")
        self.assertEqual(self._counts(harness.configuration), (0, 0, 0))
        harness.suspend()
        raw_store = self._provision()
        _, decision_text, _ = subject._canonical_decision_time(fixture.DECISION_TIME)
        description = AgentExecutionDispatchAdmission(self.grant, self.binding, decision_text)
        for untrusted in (description, subject._DispatchClassification(description, "intent")):
            with self.subTest(description=type(untrusted).__name__):
                self._assert_outcome(raw_store.admit_or_return_existing(untrusted), "invalid_input")
                self.assertEqual(self._counts(), (0, 0, 0))
