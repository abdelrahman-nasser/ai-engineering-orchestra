"""112 locked AIO-056 production scenarios; disposable ledgers, no invocation.

The raw-storage lane uses an explicitly synthetic revalidation edge on real
canonical session lifecycle objects. It does not claim provider ownership.
Canonical-ownership scenarios separately acquire the genuine Windows owner
through the predecessor's redirected disposable registry/ACL fixture.
Children are reviewed storage probes, never production executors.
"""

from __future__ import annotations

import ast
import copy
from contextlib import closing
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
import zipfile
from unittest import mock

import engineering_orchestration.sqlite_agent_execution_dispatch_admission_store as subject
import engineering_orchestration._local_dispatch_claim_lease as adapter
from engineering_orchestration.authorization_domain_ownership import AuthorizationDomainIdentity
from engineering_orchestration.agent_execution_dispatch_admission import AgentExecutionDispatchAdmission
from engineering_orchestration.agent_execution_dispatch_admission_store import _mint_revocation_request
from tests import test_atomic_durable_dispatch_outbox as outbox
from tests import test_sqlite_agent_execution_dispatch_admission_store as fixture
from tests import test_local_operational_trust as integrated
from tests import test_windows_local_authorization_domain_owner as owner_fixture


ROOT = Path(__file__).resolve().parents[1]
PARENT = Path(r"C:\Users\Abdelrahman\AppData\Local\Temp").resolve()
PYTHON = Path(r"C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe")
CLAIMS = "agent_execution_dispatch_claims"
RENEWALS = "agent_execution_dispatch_renewals"
T = fixture.DECISION_TIME
D = timedelta(seconds=30)
PROCESS_EVIDENCE = []


class _Clock(fixture.MutableClock):
    exception = None

    def now_utc(self):
        if self.exception is not None:
            self.calls += 1
            raise self.exception
        return super().now_utc()


def token(number):
    return f"{number:064x}"


class _RawResource:
    def close(self):
        pass


_ORIGINAL_REVALIDATE = adapter._WindowsOwnedAuthorizationDomainSession._revalidate


def _raw_revalidate(session):
    if type(session._registry) is not _RawResource:
        return _ORIGINAL_REVALIDATE(session)
    if session._store._verified_activation_state_for_ownership() != "active":
        raise integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError("raw fixture is inactive")


def _raw_session(store):
    identity = AuthorizationDomainIdentity(store.configuration.authorization_domain_id,
                                          store.configuration.ledger_instance_id,
                                          store.configuration.domain_generation)
    return adapter._WindowsOwnedAuthorizationDomainSession._create(
        binding=SimpleNamespace(identity=identity), registry=_RawResource(), pin=_RawResource(),
        store=store, coordinator=None, administration=None,
    )


def _snapshot(path):
    base = outbox._snapshot(path)
    with closing(outbox._connect(path)) as c:
        extra = tuple((table, tuple(tuple(row) for row in c.execute(
            f"SELECT * FROM {table} ORDER BY 1"))) for table in (CLAIMS, RENEWALS)
            if c.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?", (table,)).fetchone())
    return base, extra


def _old_ledger(configuration, version, *, nonempty=True):
    originals = outbox._make_v1(configuration, nonempty=nonempty)
    if version == 2:
        with closing(outbox._connect(configuration.database_path)) as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE admission_ledger_metadata SET migration_state='dirty'")
            migration = subject._migration_bytes()[1]
            for statement in subject._sql_statements(migration[3]):
                c.execute(statement)
            c.execute("INSERT INTO admission_schema_migrations VALUES (?,?,?)", migration[:3])
            c.execute("UPDATE admission_ledger_metadata SET schema_version=2,schema_manifest_id=?",
                      (subject._schema_manifest_id(2),))
            c.execute("PRAGMA user_version=2")
            c.execute("UPDATE admission_ledger_metadata SET migration_state='clean'")
            if nonempty:
                for index in range(2):
                    run = fixture.make_run(f"run::v2-intent-{index}")
                    grant = fixture.make_grant(bound_run=run, grant_id=f"grant::v2-intent-{index}")
                    binding = fixture.make_binding(bound_run=run)
                    _, text, key = subject._canonical_decision_time(T)
                    admission = AgentExecutionDispatchAdmission(grant, binding, text)
                    c.execute("INSERT INTO agent_execution_dispatch_admissions VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (*subject._grant_identity(grant), run.run_id, subject._encode_grant(grant),
                               subject._encode_binding(binding), subject._encode_admission(admission), text, key))
                    c.execute("INSERT INTO agent_execution_dispatch_intents VALUES (?,?,?,?)", subject._grant_identity(grant))
            c.execute("COMMIT")
            assert subject._schema_fingerprint(c) == subject._EXPECTED_SCHEMA_FINGERPRINTS[2]
    return originals


def _probe(root_text, path_text, nonce, operation, cut, instant_text, attempt_text):
    """Exact closed child entry; all writes stay on the nonce-owned ledger."""
    root = Path(root_text)
    path = Path(path_text)
    if (root.parent.resolve() != PARENT or root.resolve() != root
            or not root.name.startswith("aio-056-") or root.is_symlink() or root.is_junction()
            or path.parent.resolve() != root
            or (root / ".aio056-owner").read_text(encoding="ascii") != nonce):
        raise AssertionError("probe target containment/nonce failed")
    configuration = fixture.config_for(path)
    now = datetime.fromisoformat(instant_text)
    attempt = int(attempt_text)
    if operation == "timeout":
        (root / "ready").write_text(nonce, encoding="ascii")
        time.sleep(30)
        return
    if operation == "migrate":
        allowed = {"migration.before_transaction", "migration.after_dirty", "migration3.after_schema",
                   "migration.after_history_before_version", "migration.after_version_publication",
                   "migration.before_commit", "migration.after_commit_before_response"}
        if cut not in allowed:
            raise AssertionError("unreviewed migration cut")
        def fail(point):
            if point == cut:
                os._exit(76)
        with mock.patch.object(subject.SqliteAgentExecutionDispatchAdmissionStore,
                               "_administration_fault", side_effect=fail):
            subject.SqliteAgentExecutionDispatchAdmissionStore.migrate(
                configuration, access=fixture.administration_access(configuration))
        raise AssertionError("migration cut not reached")
    allowed = {"claim.before_transaction", "claim.after_begin", "claim.after_candidate_selection",
               "claim.after_generation_allocation", "claim.after_insert", "claim.after_watermark",
               "claim.before_commit", "claim.after_commit_before_response", "renew.before_transaction",
               "renew.after_validation", "renew.after_insert", "renew.after_watermark",
               "renew.before_commit", "renew.after_commit_before_response", "none"}
    if cut not in allowed or operation not in {"claim", "renew", "history", "held"}:
        raise AssertionError("unreviewed probe operation/cut")
    store = subject.SqliteAgentExecutionDispatchAdmissionStore(
        configuration, clock=fixture.MutableClock(now), access=fixture.store_access(configuration))
    with mock.patch.object(adapter._WindowsOwnedAuthorizationDomainSession, "_revalidate", _raw_revalidate):
        session = _raw_session(store)
        facade = adapter._create_owned_dispatch_claim_lease(session)
        def fail(point):
            if point == cut:
                os._exit(76)
        with mock.patch.object(store, "_fault", side_effect=fail):
            if operation == "claim":
                result = facade.claim(token(attempt))
            elif operation == "history":
                result = facade.query(token(attempt))
            elif operation == "held":
                with closing(outbox._connect(path)) as c:
                    c.execute("BEGIN IMMEDIATE")
                    (root / "ready").write_text(nonce, encoding="ascii")
                    os._exit(76)
            else:
                # Raw mechanics lane reproduces a stored ID only for Renewal
                # crash testing, never as canonical incarnation authority.
                history = facade.query(token(1)).claim
                object.__setattr__(facade._executor, "_executor_id", history.executor_instance_id)
                result = facade.renew(token(attempt), history.identity, history.claim_id, history.lease_generation)
        session.close()
        if cut != "none":
            raise AssertionError("crash cut not reached: " + result.outcome)
        print(json.dumps({"outcome": result.outcome,
                          "claim": None if result.claim is None else result.claim.claim_id,
                          "generation": None if result.claim is None else result.claim.lease_generation,
                          "executor": facade._executor._executor_id,
                          "history_only": result.history_only,
                          "watermark": store.watermark()}))


class DispatchClaimLeaseTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(Path(sys.executable).resolve(), PYTHON.resolve())
        self.root = Path(tempfile.mkdtemp(prefix="aio-056-", dir=PARENT)).resolve()
        self.nonce = os.urandom(32).hex()
        (self.root / ".aio056-owner").write_text(self.nonce, encoding="ascii")
        self.addCleanup(self._cleanup)
        self.sessions = []
        patcher = mock.patch.object(adapter._WindowsOwnedAuthorizationDomainSession, "_revalidate", _raw_revalidate)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._close_sessions)
        self.configuration = fixture.config_for(self.root / "dispatch.sqlite3")
        self.clock = _Clock()

    def _close_sessions(self):
        for session in self.sessions:
            if session._state in ('fencing', 'fenced') and type(session._registry) is _RawResource:
                session._state = 'lost'  # synthetic terminal-state fixture cleanup only
            session.close()

    def _cleanup(self):
        if (self.root.resolve() != self.root or self.root.parent != PARENT
                or self.root.is_symlink() or self.root.is_junction()
                or (self.root / ".aio056-owner").read_text(encoding="ascii") != self.nonce):
            raise AssertionError("refusing cleanup outside nonce-owned root")
        shutil.rmtree(self.root)

    def _open(self, configuration=None, clock=None):
        config = configuration or self.configuration
        return subject.SqliteAgentExecutionDispatchAdmissionStore(
            config, clock=clock or self.clock, access=fixture.store_access(config))

    def _setup(self, *, count=1, configuration=None):
        config = configuration or self.configuration
        result = subject.SqliteAgentExecutionDispatchAdmissionStore.provision(
            config, access=fixture.administration_access(config))
        self.assertEqual(result.outcome.value, "provisioned", result.detail)
        self.store = self._open(config)
        self.grants = [self._admit(index, self.store) for index in range(count)]
        self.facade = self._facade(self.store)
        return self.facade

    def _facade(self, store=None):
        session = _raw_session(store or self.store)
        self.sessions.append(session)
        return adapter._create_owned_dispatch_claim_lease(session)

    def _other(self, facade=None):
        return adapter._create_owned_dispatch_claim_lease((facade or self.facade)._session)

    def _admit(self, index, store):
        run = fixture.make_run(f"run::{index}")
        grant = fixture.make_grant(bound_run=run, grant_id=f"grant::{index}",
                                   domain_id=store.configuration.authorization_domain_id)
        binding = fixture.make_binding(bound_run=run)
        result = store.admit_or_return_existing(outbox._request(store.configuration, grant, binding))
        self.assertEqual(result.outcome.value, "newly_admitted", result.detail)
        return grant

    def _claim(self, number=1, facade=None):
        result = (facade or self.facade).claim(token(number))
        self.assertEqual(result.outcome, "newly_claimed", result.detail)
        return result.claim

    def _renew(self, claim, number=2, facade=None):
        return (facade or self.facade).renew(token(number), claim.identity, claim.claim_id, claim.lease_generation)

    def _current(self, claim, facade=None):
        return (facade or self.facade).query(claim.claim_id, mode="current",
                                            identity=claim.identity, lease_generation=claim.lease_generation)

    def _counts(self, config=None):
        with closing(outbox._connect((config or self.configuration).database_path)) as c:
            return tuple(c.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in (CLAIMS, RENEWALS))

    def _corrupt(self, mutation, configuration=None):
        outbox.AtomicDurableDispatchOutboxTests._corrupt(self, configuration or self.configuration, mutation)

    def _reject(self, configuration=None):
        with self.assertRaises((subject.SqliteAdmissionStoreIntegrityError,
                                subject.SqliteAdmissionStoreIncompatibleSchemaError)):
            self._open(configuration)

    def _revoke(self, grant=None):
        grant = grant or self.grants[0]
        result = self.store.revoke_or_return_existing(_mint_revocation_request(
            self.store.configuration.authorization_domain_id, grant))
        self.assertEqual(result.outcome.value, "newly_revoked", result.detail)

    def _migrate(self, config=None):
        config = config or self.configuration
        return subject.SqliteAgentExecutionDispatchAdmissionStore.migrate(
            config, access=fixture.administration_access(config))

    def _old(self, version, nonempty=True, suffix="old"):
        config = fixture.config_for(self.root / (suffix + ".sqlite3"))
        _old_ledger(config, version, nonempty=nonempty)
        return config

    def _child(self, configuration, operation, cut="none", instant=T, attempt=1, timeout=20):
        self.assertEqual(configuration.database_path.parent.resolve(), self.root)
        source = ("import sys,types; sys.path.insert(0,sys.argv[1]); "
                  "tests=types.ModuleType('tests'); tests.__path__=[sys.argv[1]+'/tests']; "
                  "sys.modules['tests']=tests; "
                  "from tests.test_dispatch_claim_lease_foundation import _probe; _probe(*sys.argv[2:])")
        command = [str(PYTHON), "-I", "-B", "-c", source, str(ROOT), str(self.root),
                   str(configuration.database_path), self.nonce, operation, cut, instant.isoformat(), str(attempt)]
        environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
        environment.update(TEMP=str(PARENT), TMP=str(PARENT))
        process = subprocess.Popen(command, cwd=self.root, env=environment, shell=False,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timed_out = False
        try:
            try:
                output, error = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                output, error = process.communicate(timeout=15)
            if operation != "timeout":
                self.assertFalse(timed_out, error.decode(errors="replace"))
                self.assertEqual(process.returncode, 0 if cut == "none" and operation != "held" else 76,
                                 error.decode(errors="replace"))
            else:
                self.assertTrue(timed_out)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=15)
            for handle in (process.stdout, process.stderr):
                handle.close()
            native = getattr(process, "_handle", None)
            if native is not None:
                native.Close()
            PROCESS_EVIDENCE.append((operation, cut, process.returncode, timed_out,
                                     process.stdout.closed and process.stderr.closed, process.poll() is not None))
        return output

    def _race(self, left, right):
        start = threading.Barrier(3)
        results, errors = [], []
        def worker(call):
            try:
                start.wait(15)
                results.append(call())
            except BaseException as error:
                errors.append(error)
        threads = [threading.Thread(target=worker, args=(call,)) for call in (left, right)]
        for thread in threads:
            thread.start()
        start.wait(15)
        for thread in threads:
            thread.join(20)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        return results

    def _predecessor(self, name):
        case = outbox.AtomicDurableDispatchOutboxTests(name)
        result = unittest.TestResult()
        case.run(result)
        self.assertEqual((result.errors, result.failures, result.skipped), ([], [], []))

    def _owner_predecessor(self, name):
        case = owner_fixture.WindowsLocalAuthorizationDomainOwnerWin32Tests(name)
        result = unittest.TestResult()
        case.run(result)
        self.assertEqual((result.errors, result.failures, result.skipped), ([], [], []))

    def _preserved_metadata(self, old, new):
        old_row = dict(old[0][1])['admission_ledger_metadata'][0]
        new_row = dict(new[0][1])['admission_ledger_metadata'][0]
        self.assertEqual(tuple(v for i, v in enumerate(old_row) if i not in (4, 5, 9)),
                         tuple(v for i, v in enumerate(new_row) if i not in (4, 5, 9)))

    def _unchanged(self, call, outcome):
        before = _snapshot(self.configuration.database_path)
        result = call()
        self.assertEqual(result.outcome, outcome, result.detail)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        return result

    def _row(self, table, identifier):
        with closing(outbox._connect(self.configuration.database_path)) as c:
            return dict(c.execute(f'SELECT * FROM {table} WHERE {"claim_id" if table == CLAIMS else "renewal_id"}=?',
                                  (token(identifier),)).fetchone())

    def _bad_rows(self, table, identifier, changes):
        original = self._row(table, identifier)
        for field, value in changes:
            with self.subTest(table=table, field=field, value=value):
                try:
                    self._corrupt(lambda c, f=field, v=value: c.execute(
                        f'UPDATE {table} SET {f}=? WHERE {"claim_id" if table == CLAIMS else "renewal_id"}=?',
                        (v, token(identifier))))
                except sqlite3.IntegrityError:
                    # STRICT storage rejects unrepresentable types even with guards disabled.
                    self.assertEqual(self._row(table, identifier), original)
                    continue
                before = _snapshot(self.configuration.database_path)
                self._reject()
                self.assertEqual(_snapshot(self.configuration.database_path), before)
                self._corrupt(lambda c, f=field: c.execute(
                    f'UPDATE {table} SET {f}=? WHERE {"claim_id" if table == CLAIMS else "renewal_id"}=?',
                    (original[f], value if field == ('claim_id' if table == CLAIMS else 'renewal_id') else token(identifier))))

    def _canonical(self):
        harness = integrated._WindowsHarness(self)
        run = integrated._make_run()
        principal, proof = harness.human_authority(run)
        admitted = harness.coordinator.admit(run=run, authenticated_principal=principal, authority_proof=proof)
        self.assertEqual(admitted.outcome.value, 'newly_admitted')
        return harness, adapter._create_owned_dispatch_claim_lease(harness.coordinator._session)

    def test_C001_fresh_v3(self):
        self._setup(count=0)
        self.assertEqual(self._counts(), (0, 0))
        with closing(outbox._connect(self.configuration.database_path)) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 3)
            self.assertEqual(subject._schema_fingerprint(c), subject._EXPECTED_SCHEMA_FINGERPRINTS[3])
            self.assertEqual(len(c.execute('SELECT * FROM admission_schema_migrations').fetchall()), 3)
        self._open()
        self.assertEqual(len(fields(AgentExecutionDispatchAdmission)), 3)

    def test_C002_empty_v2(self):
        config = self._old(2, False)
        old = _snapshot(config.database_path)
        self.assertEqual(self._migrate(config).outcome.value, 'migrated')
        self.assertEqual(self._counts(config), (0, 0))
        self.assertEqual(dict(_snapshot(config.database_path)[0][1]).keys(), dict(old[0][1]).keys())
        self.assertEqual(self._open(config).watermark(), (None, None))
        self._preserved_metadata(old, _snapshot(config.database_path))

    def test_C003_nonempty_v2(self):
        config = self._old(2)
        # A valid v2 revocation is copied from the exact predecessor fixture.
        with closing(outbox._connect(config.database_path)) as c:
            row = c.execute('SELECT * FROM agent_execution_dispatch_admissions ORDER BY grant_id LIMIT 1').fetchone()
            c.execute('INSERT INTO agent_execution_grant_revocations VALUES (?,?,?,?,?,?,?,?,?,?)',
                      (*tuple(row)[:5], row['grant_json'], row['issuer_kind'], row['issuer_id'],
                       row['decision_time'], row['decision_time_key']))
        before = _snapshot(config.database_path)
        self.assertEqual(self._migrate(config).outcome.value, 'migrated')
        for table in ('agent_execution_dispatch_admissions', 'agent_execution_grant_revocations', outbox.INTENTS, outbox.MARKERS):
            self.assertEqual(dict(_snapshot(config.database_path)[0][1])[table], dict(before[0][1])[table])
        self.assertEqual(self._counts(config), (0, 0))
        self._preserved_metadata(before, _snapshot(config.database_path))

    def test_C004_empty_v1(self):
        config = self._old(1, False)
        self.assertEqual(self._migrate(config).outcome.value, 'migrated')
        with closing(outbox._connect(config.database_path)) as c:
            self.assertEqual([r[0] for r in c.execute('SELECT migration_id FROM admission_schema_migrations ORDER BY migration_id')], [1, 2, 3])
        self.assertEqual(self._counts(config), (0, 0))

    def test_C005_nonempty_v1(self):
        config = self._old(1)
        before = _snapshot(config.database_path)
        self.assertEqual(self._migrate(config).outcome.value, 'migrated')
        with closing(outbox._connect(config.database_path)) as c:
            count = c.execute('SELECT count(*) FROM agent_execution_dispatch_admissions').fetchone()[0]
            self.assertEqual(c.execute('SELECT count(*) FROM legacy_admission_markers').fetchone()[0], count)
            self.assertEqual(c.execute('SELECT count(*) FROM agent_execution_dispatch_intents').fetchone()[0], 0)
        self.assertEqual(dict(_snapshot(config.database_path)[0][1])[outbox.ADMISSIONS], dict(before[0][1])[outbox.ADMISSIONS])
        self.assertEqual(self._counts(config), (0, 0))

    def test_C006_v2_xor(self):
        for overlap in (False, True):
            config = self._old(2, suffix='xor' + str(overlap))
            def corrupt(c):
                if overlap:
                    c.execute('INSERT INTO legacy_admission_markers SELECT *,2 FROM agent_execution_dispatch_intents LIMIT 1')
                else:
                    c.execute('DELETE FROM agent_execution_dispatch_intents')
            self._corrupt(corrupt, config)
            before = _snapshot(config.database_path)
            self.assertEqual(self._migrate(config).outcome.value, 'integrity_failure')
            self.assertEqual(_snapshot(config.database_path), before)

    def test_C007_v3_intent_guard(self):
        self._setup()
        for field, value in (('migration_state', 'dirty'), ('activation_state', 'fenced'), ('schema_version', 2)):
            with self.subTest(field=field):
                with closing(outbox._connect(self.configuration.database_path)) as c:
                    c.execute('BEGIN IMMEDIATE')
                    if field == 'schema_version':
                        triggers = c.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger'").fetchall()
                        for name, _ in triggers:
                            c.execute('DROP TRIGGER ' + name)
                    c.execute(f'UPDATE admission_ledger_metadata SET {field}=?', (value,))
                    if field == 'schema_version':
                        for _, sql in triggers:
                            c.execute(sql)
                    with self.assertRaises(sqlite3.IntegrityError):
                        c.execute('INSERT INTO agent_execution_dispatch_intents VALUES (?,?,?,?)', subject._grant_identity(self.grants[0]))
                    c.execute('ROLLBACK')
        self.assertEqual(self._counts(), (0, 0))

    def test_C008_prefix_bytes(self):
        expected = ('6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed',
                    'eee70c9d3e31dca036e716fc8b0ad42c78c97bb07cc5c6e323eaa7290e0ba6db')
        self.assertEqual(tuple(m[2] for m in subject._migration_bytes()[:2]), expected)
        self._predecessor('test_O10_migration_one_checksum_mismatch')
        self._predecessor('test_O11_packaged_migration_two_checksum_mismatch')

    def test_C009_v3_manifest(self):
        self._setup(count=0)
        migration = subject._migration_bytes()[2]
        self.assertEqual(migration[2], 'c9163740873586ab39ee760c292cdcdd07bf050ee06f37c29614c5e3a8144949')
        self.assertEqual(hashlib.sha256(migration[3]).hexdigest(), migration[2])
        for sql in ("UPDATE admission_schema_migrations SET sha256='" + '0' * 64 + "' WHERE migration_id=3",
                    "UPDATE admission_ledger_metadata SET schema_manifest_id='bad'",
                    'DROP TRIGGER agent_execution_dispatch_claims_no_update'):
            self._audit_mutation(sql)

    def _audit_mutation(self, sql):
        with closing(outbox._connect(self.configuration.database_path)) as c:
            c.execute('BEGIN IMMEDIATE')
            if sql.startswith(('UPDATE', 'DELETE', 'INSERT')):
                triggers = c.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger'").fetchall()
                for name, _ in triggers:
                    c.execute('DROP TRIGGER ' + name)
                c.execute(sql)
                for _, definition in triggers:
                    c.execute(definition)
            else:
                c.execute(sql)
            with self.assertRaises((subject.SqliteAdmissionStoreIntegrityError, subject.SqliteAdmissionStoreIncompatibleSchemaError)):
                self.store._verify_authoritative_connection(c, allow_fenced=False)
            c.execute('ROLLBACK')

    def test_C010_no_auto_migration(self):
        for version in (1, 2):
            config = self._old(version, suffix='version' + str(version))
            before = _snapshot(config.database_path)
            self._reject(config)
            self.assertEqual(_snapshot(config.database_path), before)

    def test_C011_versions(self):
        self._predecessor('test_O15_unknown_newer_schema')
        self._predecessor('test_O17_application_user_metadata_version_disagreement')
        self._setup()
        self._audit_mutation('PRAGMA user_version=0')

    def test_C012_migration_history(self):
        self._predecessor('test_O14_history_prefix_gap_rebound_extra_changed_reordered')
        self._predecessor('test_O16_dirty_or_partial_schema')
        self._setup()
        self._audit_mutation('DELETE FROM admission_schema_migrations WHERE migration_id=3')

    def _migration_crashes(self, cuts):
        for version in (1, 2):
            for cut in cuts:
                with self.subTest(version=version, cut=cut):
                    config = self._old(version, suffix='crash' + str(version) + cut.replace('.', '_'))
                    before = _snapshot(config.database_path)
                    self._child(config, 'migrate', cut)
                    self.assertEqual(_snapshot(config.database_path), before)
                    self.assertEqual(self._migrate(config).outcome.value, 'migrated')

    def test_C013_migration_early_crash(self):
        self._migration_crashes(('migration.before_transaction', 'migration.after_dirty'))

    def test_C014_migration_schema_crash(self):
        self._migration_crashes(('migration3.after_schema', 'migration.after_history_before_version'))

    def test_C015_migration_publication_crash(self):
        self._migration_crashes(('migration.after_version_publication', 'migration.before_commit'))

    def test_C016_migration_commit_unknown(self):
        for version in (1, 2):
            config = self._old(version, suffix='commit' + str(version))
            self._child(config, 'migrate', 'migration.after_commit_before_response')
            self.assertEqual(self._migrate(config).outcome.value, 'already_current')
        config = self._old(2, suffix='uncommitted')
        before = _snapshot(config.database_path)
        with mock.patch.object(subject, '_commit', side_effect=subject._CommitUnknown('lost before commit')):
            self.assertEqual(self._migrate(config).outcome.value, 'commit_unknown')
        self.assertEqual(_snapshot(config.database_path), before)
        self.assertEqual(self._migrate(config).outcome.value, 'migrated')

    def test_C017_current_retry(self):
        self._setup()
        before = _snapshot(self.configuration.database_path)
        self.assertEqual(self._migrate().outcome.value, 'already_current')
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_C018_admin_authority(self):
        self._predecessor('test_O19_wrong_missing_admin_authority_or_file_pin')
        self._setup()
        self.store.fence()
        self.assertNotEqual(self._migrate().outcome.value, 'migrated')

    def test_C019_canonical_quiescence(self):
        self._predecessor('test_O54_administrative_quiescence')

    def test_C020_migration_corruption(self):
        self._predecessor('test_O58_corrupt_source_payload_revocation_watermark')
        self._predecessor('test_O13_destination_fingerprint_mismatch')

    def test_C021_canonical_first_claim(self):
        harness, facade = self._canonical()
        result = facade.claim(token(1))
        self.assertEqual(result.outcome, 'newly_claimed', result.detail)
        self.assertEqual(result.claim.lease_generation, 1)
        self.assertEqual(result.claim.lease_until_key - result.claim.acquired_at_key, 30_000_000)
        self.assertEqual(harness.coordinator._session._store.watermark()[0], result.claim.acquired_at)

    def test_C022_deterministic_order(self):
        self._setup(count=12)
        identities = sorted(subject._grant_identity(g) for g in self.grants)
        self.assertEqual([self._claim(i + 1).identity for i in range(12)], identities)
        self.clock.value += timedelta(seconds=1)
        later = self._admit(99, self.store)
        self.assertEqual(self._claim(99).identity, subject._grant_identity(later))
        # Older Admission precedes lexically earlier newer identity.
        earlier = self._admit(101, self.store)
        self.clock.value += timedelta(microseconds=1)
        later = self._admit(-1, self.store)
        self.assertEqual(self._claim(101).identity, subject._grant_identity(earlier))
        self.assertEqual(self._claim(102).identity, subject._grant_identity(later))

    def test_C023_empty_legacy_untimed(self):
        self._setup(count=0)
        self.clock.exception = RuntimeError('must not sample')
        self._unchanged(lambda: self.facade.claim(token(1)), 'empty')
        config = self._old(1)
        self._migrate(config)
        facade = self._facade(self._open(config))
        self.assertEqual(facade.claim(token(2)).outcome, 'empty')

    def test_C024_revoked_untimed(self):
        self._setup()
        self._revoke()
        self.clock.exception = RuntimeError('must not sample')
        self._unchanged(lambda: self.facade.claim(token(1)), 'authority_ineligible')

    def test_C025_mixed_candidates(self):
        self._setup(count=4)
        ordered = sorted(self.grants, key=subject._grant_identity)
        self._revoke(ordered[0])
        first = self._claim()
        self.assertEqual(first.identity, subject._grant_identity(ordered[1]))
        self.clock.value += D
        self.assertEqual(self._claim(2, self._other()).identity, first.identity)
        self.assertEqual(self._claim(3).identity, subject._grant_identity(ordered[2]))

    def test_C026_all_active_watermark(self):
        self._setup()
        self._claim()
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self.facade.claim(token(2)).outcome, 'temporarily_unavailable')
        self.assertEqual(self._counts(), (1, 0))
        self.assertEqual(self.store.watermark()[0], subject._canonical_decision_time(self.clock.value)[1])
        self.assertEqual(self.facade.query(token(2)).outcome, 'claim_not_found')

    def test_C027_claim_retry_history(self):
        self._setup()
        claim = self._claim()
        self.clock.value += D
        self._claim(2, self._other())
        self._revoke()
        self.clock.exception = RuntimeError('history only')
        result = self._unchanged(lambda: self.facade.claim(token(1)), 'existing_claim_history')
        self.assertEqual(result.claim, claim)
        self.assertTrue(result.history_only)

    def test_C028_conflicting_executor_retry(self):
        self._setup()
        self._claim()
        result = self._unchanged(lambda: self._other().claim(token(1)), 'claim_identity_conflict')
        self.assertIsNone(result.claim)

    def test_C029_no_row_reevaluation(self):
        self._setup(count=0)
        self.assertEqual(self.facade.claim(token(1)).outcome, 'empty')
        self._admit(1, self.store)
        self._claim()
        self.assertEqual(self._counts(), (1, 0))

    def test_C030_bad_request(self):
        self._setup()
        for value in (None, True, 1, '', 'a' * 63, 'A' * 64, 'g' * 64, ['a' * 64]):
            self._unchanged(lambda v=value: self.facade.claim(v), 'invalid_input')
        self.assertEqual(self.store._claim_dispatch_intent(SimpleNamespace()).outcome, 'invalid_input')
        with self.assertRaises(TypeError):
            subject._DispatchRequest()
        with self.facade._session.operation():
            request = subject._mint_dispatch_request('claim', self.facade._session, self.store,
                                                    capability=self.facade._executor, claim_id=token(1))
            for call in (copy.copy, copy.deepcopy, pickle.dumps):
                with self.assertRaises(TypeError):
                    call(request)

    def test_C031_claim_closed_signature(self):
        self._setup()
        self.assertEqual(tuple(inspect.signature(self.facade.claim).parameters), ('claim_id',))
        for name in ('identity', 'time', 'duration', 'generation', 'run', 'tool', 'owned'):
            with self.assertRaises(TypeError):
                self.facade.claim(token(1), **{name: True})

    def test_C032_exact_expiry(self):
        self._setup()
        old = self._claim()
        self.clock.value = T + D - timedelta(microseconds=1)
        self.assertEqual(self._other().claim(token(2)).outcome, 'temporarily_unavailable')
        self.clock.value = T + D
        new = self._claim(2, self._other())
        self.assertEqual(new.lease_generation, 2)
        self.assertEqual(self.facade.query(old.claim_id).claim, old)

    def test_C033_contiguous_restart(self):
        self._setup()
        for generation in range(1, 5):
            self.clock.value = T + (generation - 1) * D
            facade = self._facade(self._open())
            self.assertEqual(self._claim(generation, facade).lease_generation, generation)
        self.assertEqual(self._counts(), (4, 0))

    def test_C034_predecessor_id(self):
        self._setup()
        claim = self._claim()
        self.clock.value += D
        result = self._unchanged(lambda: self.facade.claim(claim.claim_id), 'existing_claim_history')
        self.assertEqual(result.claim.lease_generation, 1)
        self.assertEqual(self._claim(2, self._other()).lease_generation, 2)

    def test_C035_generation_exhaustion(self):
        self.assertEqual(subject._next_dispatch_integer(2**63 - 2), 2**63 - 1)
        with self.assertRaises(OverflowError):
            subject._next_dispatch_integer(2**63 - 1)
        self._setup(count=2)
        self._claim()
        self.clock.value += D
        # Test-only lowered limit on a real contiguous one-row chain.
        with mock.patch.object(subject, '_DISPATCH_MAX_INTEGER', 1):
            self._unchanged(lambda: self._other().claim(token(2)), 'generation_exhausted')

    def test_C036_same_executor_live(self):
        self._setup()
        self._claim()
        self._unchanged(lambda: self.facade.claim(token(2)), 'temporarily_unavailable')

    def test_C037_consumed_grant_expiry(self):
        self._setup()
        self.clock.value = T + timedelta(hours=2)
        self._claim()

    def test_C038_bound_store(self):
        self._setup()
        for field, value in (('authorization_domain_id', 'wrong'), ('ledger_instance_id', 'wrong'), ('domain_generation', 99)):
            old = self.store.configuration
            self.store.configuration = replace(old, **{field: value})
            self.assertIn(self.facade.claim(token(1)).outcome, ('ownership_lost', 'integrity_failure'))
            self.store.configuration = old
            # Terminal session loss cannot be repaired; compose a new raw fixture.
            self.facade = self._facade()
        wrong = self._old(1, suffix='wrongpin')
        self.assertNotEqual(wrong.database_path, self.configuration.database_path)
        self._predecessor('test_O39_domain_ledger_instance_generation_mismatch')
        self._owner_predecessor('test_copy_move_and_replacement_do_not_match_the_bound_identity')

    def test_C039_renewal(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        result = self._renew(claim)
        self.assertEqual(result.outcome, 'newly_renewed', result.detail)
        self.assertEqual(result.renewal.renewal_sequence, 1)
        self.assertEqual(result.renewal.lease_until_key - result.renewal.renewed_at_key, 30_000_000)

    def test_C040_renewal_chain(self):
        self._setup()
        claim = self._claim()
        rows = []
        for sequence in range(1, 5):
            self.clock.value += timedelta(seconds=1)
            result = self._renew(claim, sequence + 1)
            self.assertEqual(result.outcome, 'newly_renewed')
            self.assertEqual(result.renewal.renewal_sequence, sequence)
            rows.append(result.renewal)
        self.assertEqual(self.facade.query(claim.claim_id).renewals, tuple(rows))
        self.assertEqual([r.lease_until_key for r in rows], sorted(set(r.lease_until_key for r in rows)))

    def test_C041_renewal_retry(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        original = self._renew(claim).renewal
        self.clock.value += timedelta(seconds=10)
        self.clock.exception = RuntimeError('retry must not sample')
        result = self._unchanged(lambda: self._renew(claim), 'existing_renewal_history')
        self.assertEqual(result.renewal, original)

    def test_C042_old_renewal_history(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        renewal = self._renew(claim).renewal
        self.clock.value += D
        self._claim(3, self._other())
        self._revoke()
        self.clock.exception = RuntimeError('history only')
        result = self._unchanged(lambda: self._renew(claim), 'existing_renewal_history')
        self.assertEqual(result.renewal, renewal)
        self.assertTrue(result.history_only)

    def test_C043_renewal_rebinding(self):
        self._setup(count=2)
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        tuples = [(token(99), claim.identity, 1, self.facade),
                  (claim.claim_id, subject._grant_identity(self.grants[1]), 1, self.facade),
                  (claim.claim_id, claim.identity, 2, self.facade),
                  (claim.claim_id, claim.identity, 1, self._other())]
        for identifier, identity, generation, facade in tuples:
            self._unchanged(lambda: facade.renew(token(2), identity, identifier, generation), 'renewal_identity_conflict')
        for index, value in ((0, 'domain::wrong'), (1, 'human'), (2, 'issuer::wrong'), (3, 'grant::wrong')):
            identity = list(claim.identity)
            identity[index] = value
            expected = 'invalid_input' if index == 0 else 'renewal_identity_conflict'
            self._unchanged(lambda: self.facade.renew(token(2), tuple(identity), claim.claim_id, 1), expected)

    def test_C044_missing_mismatch(self):
        self._setup()
        claim = self._claim()
        self._unchanged(lambda: self.facade.renew(token(2), claim.identity, token(99), 1), 'claim_not_found')
        self._unchanged(lambda: self.facade.renew(token(2), claim.identity, claim.claim_id, 2), 'claim_identity_conflict')

    def test_C045_stale(self):
        self._setup()
        old = self._claim()
        self.clock.value += D
        self._claim(2, self._other())
        self._unchanged(lambda: self._renew(old, 3), 'stale_generation')

    def test_C046_expired_renewal(self):
        self._setup()
        claim = self._claim()
        for delta in (D, D + timedelta(microseconds=1)):
            self.clock.value = T + delta
            self.assertEqual(self._renew(claim).outcome, 'expired_claim')
            self.assertEqual(self._counts(), (1, 0))

    def test_C047_nonextending(self):
        self._setup()
        claim = self._claim()
        self._unchanged(lambda: self._renew(claim), 'nonextending')
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self._unchanged(lambda: self._renew(claim, 3), 'nonextending')

    def test_C048_nonextending_reevaluation(self):
        self._setup()
        claim = self._claim()
        self.assertEqual(self._renew(claim).outcome, 'nonextending')
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self._renew(claim).outcome, 'newly_renewed')
        self.assertEqual(self._counts(), (1, 1))

    def test_C049_no_banking(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=10)
        renewal = self._renew(claim).renewal
        self.assertEqual(renewal.lease_until_key - claim.lease_until_key, 10_000_000)

    def test_C050_revocation_orders(self):
        self._setup(count=2)
        first, second = self._claim(), self._claim(2)
        self.clock.value += timedelta(seconds=1)
        grant = next(g for g in self.grants if subject._grant_identity(g) == first.identity)
        self._revoke(grant)
        self._unchanged(lambda: self._renew(first, 3), 'revoked')
        result = self._renew(second, 4)
        self.assertEqual(result.outcome, 'newly_renewed')
        self._revoke(next(g for g in self.grants if subject._grant_identity(g) == second.identity))
        self.assertEqual(self.facade.query(second.claim_id).renewals, (result.renewal,))

    def test_C051_sequence_exhaustion(self):
        with self.assertRaises(OverflowError):
            subject._next_dispatch_integer(2**63 - 1)
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self.clock.value += timedelta(seconds=1)
        with mock.patch.object(subject, '_DISPATCH_MAX_INTEGER', 1):
            self._unchanged(lambda: self._renew(claim, 3), 'sequence_exhausted')
        self.clock.value = T + D + timedelta(seconds=1)
        second = self._claim(4)
        self.clock.value += timedelta(seconds=1)
        with mock.patch.object(subject, '_DISPATCH_MAX_INTEGER', 2):
            self.assertEqual(self._renew(second, 5).outcome, 'newly_renewed')

    def test_C052_wrong_executor(self):
        self._setup()
        claim = self._claim()
        other = self._other()
        self.assertNotEqual(other.executor_instance_id, claim.executor_instance_id)
        self._unchanged(lambda: self._renew(claim, facade=other), 'claim_identity_conflict')

    def test_C053_renewal_grammar(self):
        self._setup()
        claim = self._claim()
        for generation in (True, False, 0, -1, 1.0, '1', 2**63):
            self._unchanged(lambda: self.facade.renew(token(2), claim.identity, claim.claim_id, generation), 'invalid_input')
        for value in (None, True, '', 'A' * 64, 'a' * 65):
            self._unchanged(lambda: self.facade.renew(value, claim.identity, claim.claim_id, 1), 'invalid_input')

    def test_C054_renewal_signature(self):
        self._setup()
        self.assertEqual(tuple(inspect.signature(self.facade.renew).parameters),
                         ('renewal_id', 'identity', 'claim_id', 'lease_generation'))
        with self.assertRaises(TypeError):
            self.facade.renew(token(2), ('a', 'human', 'b', 'c'), token(1), 1, duration=30)

    def _timed_paths(self, bad, expected, *, exception=False):
        self._setup(count=2)
        claim = self._claim()
        self.clock.value = T + timedelta(seconds=1)
        calls = (lambda: self.facade.claim(token(3)), lambda: self._renew(claim), lambda: self._current(claim))
        for call in calls:
            with self.subTest(operation=call):
                if exception:
                    self.clock.exception = bad
                else:
                    self.clock.value = bad
                self._unchanged(call, expected)
                self.clock.exception = None
                self.clock.value = T + timedelta(seconds=1)
        self.assertEqual(self._renew(claim).outcome, 'newly_renewed')
        self.assertEqual(self._current(claim).outcome, 'current_claim')
        self._claim(3)

    def test_C055_equal_watermark(self):
        self._setup(count=2)
        claim = self._claim()
        self._claim(2)
        self.assertEqual(self._current(claim).outcome, 'current_claim')
        self.clock.value += timedelta(microseconds=1)
        self.assertEqual(self._renew(claim, 3).outcome, 'newly_renewed')
        self.assertEqual(self._current(claim).outcome, 'current_claim')
        self.assertEqual(self._renew(claim, 4).outcome, 'nonextending')

    def test_C056_clock_rollback(self):
        self._timed_paths(T - timedelta(microseconds=1), 'clock_regression')

    def test_C057_clock_exception(self):
        self._timed_paths(RuntimeError('trusted clock failed'), 'clock_failure', exception=True)

    def test_C058_clock_types(self):
        self._setup(count=2)
        claim = self._claim()
        for bad in (None, True, '2026-09-23T10:30:00Z', T.replace(tzinfo=None),
                    T.astimezone(timezone(timedelta(hours=1))), T.timestamp()):
            self.clock.value = bad
            for call in (lambda: self.facade.claim(token(3)), lambda: self._renew(claim), lambda: self._current(claim)):
                self._unchanged(call, 'clock_failure')

    def test_C059_forward_jump(self):
        self._setup()
        old = self._claim()
        self.clock.value += timedelta(days=300)
        other = self._other()
        new = self._claim(2, other)
        self._unchanged(lambda: self._renew(old, 3), 'stale_generation')
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self._renew(new, 4, other).outcome, 'newly_renewed')
        self.clock.value -= timedelta(microseconds=1)
        self._unchanged(lambda: self._current(new, other), 'clock_regression')

    def test_C060_time_overflow(self):
        self._setup()
        self.clock.value = datetime.max.replace(tzinfo=timezone.utc)
        self._unchanged(lambda: self.facade.claim(token(1)), 'clock_failure')
        with self.assertRaises((ValueError, OverflowError)):
            subject._dispatch_expiry(datetime.max.replace(tzinfo=timezone.utc))
        self.clock.value = T
        claim = self._claim()
        with mock.patch.object(subject, '_dispatch_expiry', side_effect=OverflowError('addition overflow')):
            self.clock.value += timedelta(seconds=1)
            self._unchanged(lambda: self._renew(claim), 'clock_failure')

    def test_C061_canonical_calendar(self):
        for instant in (datetime(1, 1, 1, tzinfo=timezone.utc), datetime(2024, 2, 29, 23, 59, 59, 999999, timezone.utc),
                        datetime(2025, 12, 31, 23, 59, 59, 999999, timezone.utc), T):
            _, text, key = subject._canonical_decision_time(instant)
            self.assertEqual(len(text), 27)
            self.assertEqual(subject._parse_decision_time(text), (instant, key))
            if key + 30_000_000 <= subject._DISPATCH_MAX_TIME_KEY:
                expiry, expiry_key = subject._dispatch_expiry(instant)
                self.assertEqual(subject._parse_decision_time(expiry)[0], instant + D)
                self.assertEqual(expiry_key, key + 30_000_000)

    def test_C062_shared_watermark(self):
        self._setup(count=2)
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._admit(99, self.store)
        self.clock.value += timedelta(seconds=1)
        renewal = self._renew(claim).renewal
        self.clock.value += timedelta(seconds=1)
        self._revoke(self.grants[1])
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self._current(claim).outcome, 'current_claim')
        watermark = subject._parse_decision_time(self.store.watermark()[0])[1]
        self.assertGreater(watermark, renewal.renewed_at_key)
        self.assertLess(watermark, renewal.lease_until_key)
        self._open()

    def test_C063_half_open(self):
        self._setup()
        claim = self._claim()
        for delta, outcome in ((timedelta(microseconds=-1), 'clock_regression'),
                               (D - timedelta(microseconds=1), 'current_claim'),
                               (D, 'expired_claim'), (D + timedelta(microseconds=1), 'expired_claim')):
            self.clock.value = T + delta
            self.assertEqual(self._current(claim).outcome, outcome)

    def test_C064_history_no_clock(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        renewal = self._renew(claim).renewal
        self.clock.exception = RuntimeError('must not read clock')
        self.assertEqual(self._unchanged(lambda: self.facade.query(claim.claim_id), 'claim_history').renewals, (renewal,))
        self._unchanged(lambda: self.facade.claim(claim.claim_id), 'existing_claim_history')
        self._unchanged(lambda: self._renew(claim), 'existing_renewal_history')

    def test_C065_negative_commit_unknown(self):
        self._setup()
        self._claim()
        self.clock.value += timedelta(seconds=1)
        real = subject._commit
        def committed(c):
            real(c)
            raise subject._CommitUnknown('response lost')
        for effect in (committed, lambda c: (_ for _ in ()).throw(subject._CommitUnknown('not committed'))):
            with mock.patch.object(subject, '_commit', side_effect=effect):
                self.assertEqual(self.facade.claim(token(2)).outcome, 'commit_unknown')
            self.assertEqual(self.facade.query(token(2)).outcome, 'claim_not_found')
        self.clock.value = T + D
        self._claim(2)

    def test_C066_process_history(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        renewal = self._renew(claim).renewal
        before = _snapshot(self.configuration.database_path)
        result = json.loads(self._child(self.configuration, 'history'))
        self.assertEqual(result['outcome'], 'claim_history')
        self.assertTrue(result['history_only'])
        self.assertNotEqual(result['executor'], claim.executor_instance_id)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self.assertEqual(self.facade.query(claim.claim_id).renewals, (renewal,))

    def test_C067_claim_parent(self):
        self._setup()
        self._claim()
        for sql in ('DELETE FROM agent_execution_dispatch_intents',
                    'INSERT INTO legacy_admission_markers SELECT *,2 FROM agent_execution_dispatch_intents'):
            self._corrupt(lambda c: c.execute(sql))
            self._reject()
            self._corrupt(lambda c: (c.execute('DELETE FROM legacy_admission_markers'),
                                    c.execute('INSERT OR IGNORE INTO agent_execution_dispatch_intents SELECT authorization_domain_id,issuer_kind,issuer_id,grant_id FROM agent_execution_dispatch_admissions')))
        self._corrupt(lambda c: (c.execute('INSERT INTO legacy_admission_markers SELECT *,2 FROM agent_execution_dispatch_intents'),
                                c.execute('DELETE FROM agent_execution_dispatch_intents')))
        self._reject()  # coherent legacy classification still cannot parent Claim

    def test_C068_orphan_renewal(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        with closing(outbox._connect(self.configuration.database_path)) as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DROP TRIGGER agent_execution_dispatch_renewals_history_insert_guard')
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'FOREIGN KEY'):
                c.execute(f'INSERT INTO {RENEWALS} SELECT ?,?,authorization_domain_id,issuer_kind,issuer_id,grant_id,executor_instance_id,lease_generation,renewal_sequence,renewed_at,renewed_at_key,lease_until,lease_until_key FROM {RENEWALS}', (token(3), token(99)))
            c.execute('ROLLBACK')
        self._corrupt(lambda c: c.execute(f'DELETE FROM {CLAIMS}'))
        self._reject()

    def test_C069_composites(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        for table, identifier in ((CLAIMS, 1), (RENEWALS, 2)):
            self._bad_rows(table, identifier, [('authorization_domain_id', 'wrong'), ('issuer_kind', 'human'),
                                              ('issuer_id', 'wrong'), ('grant_id', 'wrong')])

    def test_C070_renewal_exact_parent(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self._bad_rows(RENEWALS, 2, [('claim_id', token(99)), ('executor_instance_id', token(99)), ('lease_generation', 2)])

    def test_C071_duplicates(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        for table in (CLAIMS, RENEWALS):
            for verb in ('INSERT', 'INSERT OR REPLACE'):
                with closing(outbox._connect(self.configuration.database_path)) as c:
                    with self.assertRaises(sqlite3.IntegrityError):
                        c.execute(f'{verb} INTO {table} SELECT * FROM {table}')
                    columns = [r[1] for r in c.execute(f'PRAGMA table_info({table})')]
                    projection = ','.join('?' if i == 0 else col for i, col in enumerate(columns))
                    with self.assertRaises(sqlite3.IntegrityError):
                        c.execute(f'{verb} INTO {table} SELECT {projection} FROM {table}', (token(99),))
        self.assertEqual(self._counts(), (1, 1))

    def test_C072_every_column_immutable(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        with closing(outbox._connect(self.configuration.database_path)) as c:
            for table in (CLAIMS, RENEWALS):
                for column in (r[1] for r in c.execute(f'PRAGMA table_info({table})')):
                    with self.subTest(table=table, column=column), self.assertRaises(sqlite3.IntegrityError):
                        c.execute(f'UPDATE {table} SET {column}={column}')
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(f'DELETE FROM {table}')

    def test_C073_generation_corruption(self):
        self._setup()
        self._claim()
        self._bad_rows(CLAIMS, 1, [('lease_generation', n) for n in (0, -1, 2, 3, 'bad')])
        for n in (True, 2**63, 1.0):
            with self.assertRaises(ValueError):
                subject._dispatch_integer(n)

    def test_C074_sequence_corruption(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self._bad_rows(RENEWALS, 2, [('renewal_sequence', n) for n in (0, -1, 2, 3, 'bad')])
        with self.assertRaises(ValueError):
            subject._dispatch_integer(2**63)
        with closing(outbox._connect(self.configuration.database_path)) as c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute(f'INSERT INTO {RENEWALS} SELECT * FROM {RENEWALS}')

    def test_C075_overlap(self):
        self._setup()
        self._claim()
        self.clock.value += D
        new = self._claim(2, self._other())
        def corrupt(c):
            c.execute(f'UPDATE {CLAIMS} SET acquired_at=?,acquired_at_key=?,lease_until=?,lease_until_key=? WHERE claim_id=?',
                      (subject._canonical_decision_time(T)[1], new.acquired_at_key - 30_000_000,
                       subject._canonical_decision_time(T + D)[1], new.lease_until_key - 30_000_000, new.claim_id))
        self._corrupt(corrupt)
        self._reject()

    def test_C076_renewal_ordering(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        row = self._row(RENEWALS, 2)
        for instant in (T - timedelta(microseconds=1), T + D, T + D + timedelta(seconds=1)):
            _, text, key = subject._canonical_decision_time(instant)
            expiry, expiry_key = subject._dispatch_expiry(instant)
            self._corrupt(lambda c: c.execute(f'UPDATE {RENEWALS} SET renewed_at=?,renewed_at_key=?,lease_until=?,lease_until_key=?',
                                              (text, key, expiry, expiry_key)))
            self._reject()
            self._corrupt(lambda c: c.execute(f'UPDATE {RENEWALS} SET renewed_at=?,renewed_at_key=?,lease_until=?,lease_until_key=?',
                                              tuple(row[k] for k in ('renewed_at', 'renewed_at_key', 'lease_until', 'lease_until_key'))))
        self.clock.value = T + D + timedelta(seconds=1)
        self._claim(3, self._other())
        # Moving the old renewal past successor acquisition must fail full audit.
        instant = self.clock.value + timedelta(seconds=1)
        _, text, key = subject._canonical_decision_time(instant)
        expiry, expiry_key = subject._dispatch_expiry(instant)
        self._corrupt(lambda c: c.execute(f'UPDATE {RENEWALS} SET renewed_at=?,renewed_at_key=?,lease_until=?,lease_until_key=?', (text, key, expiry, expiry_key)))
        self._reject()
        config = fixture.config_for(self.root / 'ordering-previous-renewal.sqlite3')
        self.clock.value = T
        self._setup(configuration=config)
        claim = self._claim()
        for number in (2, 3):
            self.clock.value += timedelta(seconds=1)
            self.assertEqual(self._renew(claim, number).outcome, 'newly_renewed')
        instant = T + timedelta(microseconds=500000)
        _, text, key = subject._canonical_decision_time(instant)
        expiry, expiry_key = subject._dispatch_expiry(instant)
        self._corrupt(lambda c: c.execute(f'UPDATE {RENEWALS} SET renewed_at=?,renewed_at_key=?,lease_until=?,lease_until_key=? WHERE renewal_id=?',
                                          (text, key, expiry, expiry_key, token(3))), config)
        self._reject(config)
        # An equal-time renewal with exactly the original expiry is nonextending.
        _, text, key = subject._canonical_decision_time(T)
        expiry, expiry_key = subject._dispatch_expiry(T)
        self._corrupt(lambda c: c.execute(f'UPDATE {RENEWALS} SET renewed_at=?,renewed_at_key=?,lease_until=?,lease_until_key=?', (text, key, expiry, expiry_key)))
        self._reject()

    def test_C077_arithmetic(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        for table, identifier in ((CLAIMS, 1), (RENEWALS, 2)):
            row = self._row(table, identifier)
            expiry = subject._parse_decision_time(row['lease_until'])[0] + timedelta(microseconds=1)
            _, text, key = subject._canonical_decision_time(expiry)
            self._corrupt(lambda c: c.execute(f'UPDATE {table} SET lease_until=?,lease_until_key=?', (text, key)))
            self._reject()  # canonical consistent text/key, wrong fixed D
            self._corrupt(lambda c: c.execute(f'UPDATE {table} SET lease_until=?,lease_until_key=?', (row['lease_until'], row['lease_until_key'])))
            self._bad_rows(table, identifier, [('lease_until_key', row['lease_until_key'] + 1),
                                              ('lease_until', claim.acquired_at)])
        self._bad_rows(RENEWALS, 2, [('renewed_at_key', claim.acquired_at_key)])

    def test_C078_persisted_grammar(self):
        self._setup()
        self._claim()
        self._bad_rows(CLAIMS, 1, [('acquired_at', '2026-02-30T00:00:00.000000Z'),
                                  ('acquired_at', '2026-09-23T10:30:00Z'), ('claim_id', 'A' * 64),
                                  ('executor_instance_id', 'bad'), ('issuer_kind', 'provider')])
        claim = self.facade.query(token(1)).claim
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self._bad_rows(RENEWALS, 2, [('renewal_id', 'A' * 64), ('renewed_at', '2026-02-30T00:00:00.000000Z'),
                                    ('lease_until', 'bad'), ('claim_id', 'bad'), ('executor_instance_id', 'bad'),
                                    ('issuer_kind', 'provider')])

    def test_C079_watermark_decisions(self):
        self._setup()
        self.clock.value += timedelta(seconds=1)
        claim = self._claim()
        for instant in (T,):
            _, text, key = subject._canonical_decision_time(instant)
            self._corrupt(lambda c: c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?', (text, key)))
            self._reject()
        _, text, key = subject._canonical_decision_time(self.clock.value)
        self._corrupt(lambda c: c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?', (text, key)))
        self._open()
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        self._corrupt(lambda c: c.execute('UPDATE admission_ledger_metadata SET last_decision_time=?,last_decision_time_key=?', (text, key)))
        self._reject()

    def test_C080_unrelated_corruption(self):
        self._setup(count=2)
        first = self._claim()
        self._claim(2)
        self._corrupt(lambda c: c.execute(f'UPDATE {CLAIMS} SET executor_instance_id=? WHERE claim_id=?', ('bad', token(2))))
        for call in (lambda: self.facade.query(first.claim_id), lambda: self.facade.claim(token(3))):
            # First call encounters the full audit; terminal loss also fences the second.
            self.assertIn(call().outcome, ('integrity_failure', 'ownership_lost'))

    def test_C081_parent_payload(self):
        self._predecessor('test_O36_wrong_admission_identity_or_parent')
        self._predecessor('test_O37_run_relationship_mismatch')

    def test_C082_schema_corruption(self):
        self._setup()
        for sql in ('CREATE TABLE extra (x)', 'CREATE INDEX extra ON agent_execution_dispatch_claims(executor_instance_id)',
                    'DROP TRIGGER agent_execution_dispatch_renewals_history_insert_guard', 'DROP TABLE agent_execution_dispatch_claims',
                    "UPDATE admission_schema_migrations SET sha256='" + '0' * 64 + "' WHERE migration_id=3",
                    "UPDATE admission_ledger_metadata SET migration_state='dirty'"):
            self._audit_mutation(sql)
        # SEC-056-1: these legal names are not SQLite's literal sqlite_ prefix.
        for prefix in ('sqliteX', 'sqliteA', 'sqlite1', 'sqlite-', 'sqlite.'):
            with self.subTest(user_trigger_prefix=prefix):
                self._audit_mutation(
                    'CREATE TRIGGER "' + prefix + '_sec056_suppress_claim" '
                    'BEFORE INSERT ON agent_execution_dispatch_claims '
                    'BEGIN SELECT RAISE(IGNORE); END')
        # Commit the reviewer's suppressing trigger only on this disposable
        # ledger. Operational verification must reject it without any repair.
        name = 'sqliteX_sec056_suppress_claim'
        definition = ('CREATE TRIGGER ' + name + ' '
                      'BEFORE INSERT ON agent_execution_dispatch_claims '
                      'BEGIN SELECT RAISE(IGNORE); END')
        with closing(outbox._connect(self.configuration.database_path)) as c:
            self.assertTrue(c.execute(
                "SELECT name FROM sqlite_schema WHERE substr(name, 1, 7) = 'sqlite_'").fetchall())
            self.assertEqual(subject._schema_fingerprint(c), subject._EXPECTED_SCHEMA_FINGERPRINTS[3])
            c.execute(definition)
            self.assertEqual(tuple(c.execute(
                'SELECT type, name, tbl_name, sql FROM sqlite_schema WHERE name=?', (name,)).fetchone()),
                ('trigger', name, CLAIMS, definition))
            self.assertNotEqual(subject._schema_fingerprint(c), subject._EXPECTED_SCHEMA_FINGERPRINTS[3])
            with self.assertRaises(subject.SqliteAdmissionStoreIntegrityError):
                self.store._verify_authoritative_connection(c, allow_fenced=False)
        before = _snapshot(self.configuration.database_path)
        calls = self.clock.calls
        self._reject()
        result = self.facade.claim(token(1))
        self.assertIn(result.outcome, ('integrity_failure', 'ownership_lost'))
        self.assertIsNone(result.claim)
        self.assertIsNone(result.renewal)
        self.assertEqual(result.renewals, ())
        self.assertEqual(self._counts(), (0, 0))
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(_snapshot(self.configuration.database_path), before)

    def test_C083_revocation_integrity(self):
        self._setup()
        claim = self._claim()
        self._revoke()
        self.assertEqual(self.facade.query(claim.claim_id).claim, claim)
        self._corrupt(lambda c: c.execute("UPDATE agent_execution_grant_revocations SET revoker_id='wrong'"))
        self._reject()
        self._predecessor('test_O58_corrupt_source_payload_revocation_watermark')

    def test_C084_bound_values_and_shape(self):
        self._setup(count=0)
        run = fixture.make_run("run';DROP TABLE x;--")
        grant = fixture.make_grant(bound_run=run, grant_id="grant';DROP TABLE x;--")
        binding = fixture.make_binding(bound_run=run)
        self.assertEqual(self.store.admit_or_return_existing(outbox._request(self.configuration, grant, binding)).outcome.value, 'newly_admitted')
        claim = self._claim()
        self.assertEqual(claim.identity[3], grant.grant_id)
        self._unchanged(lambda: self.facade.query(claim.claim_id, mode='unknown'), 'invalid_input')
        with mock.patch.object(self.store, '_query_dispatch_claim', return_value=SimpleNamespace(outcome='claim_history')):
            self.assertEqual(self.facade.query(claim.claim_id).outcome, 'integrity_failure')
        self.clock.value += timedelta(seconds=1)
        self._renew(claim)
        good = self.facade.query(claim.claim_id)
        malformed = (replace(good, history_only=False), replace(good, retry='wrong'),
                     replace(good, claim=replace(claim, lease_generation=0)),
                     replace(good, renewals=(replace(good.renewals[0], renewal_sequence=2),)))
        for bad in malformed:
            with mock.patch.object(self.store, '_query_dispatch_claim', return_value=bad):
                self.assertEqual(self.facade.query(claim.claim_id).outcome, 'integrity_failure')

    def _lease_crashes(self, operation, cuts, *, reclaim=False):
        for index, cut in enumerate(cuts):
            with self.subTest(operation=operation, cut=cut):
                config = fixture.config_for(self.root / ('lease-crash' + str(index) + '.sqlite3'))
                self._setup(configuration=config)
                instant, attempt = T, 1
                if operation == 'renew' or reclaim:
                    self._claim()
                    instant, attempt = T + (D if reclaim else timedelta(seconds=1)), 2
                before = _snapshot(config.database_path)
                self._child(config, operation, cut, instant, attempt)
                if cut.endswith('after_commit_before_response'):
                    self.assertNotEqual(_snapshot(config.database_path), before)
                    self.assertEqual(self._counts(config), (1, 1) if operation == 'renew' else (2 if reclaim else 1, 0))
                else:
                    self.assertEqual(_snapshot(config.database_path), before)
                self._open(config)

    def test_C085_claim_crashes(self):
        self._lease_crashes('claim', ('claim.before_transaction', 'claim.after_candidate_selection', 'claim.after_insert',
                                     'claim.after_watermark', 'claim.before_commit', 'claim.after_commit_before_response'))

    def test_C086_renewal_crashes(self):
        self._lease_crashes('renew', ('renew.before_transaction', 'renew.after_validation', 'renew.after_insert',
                                     'renew.after_watermark', 'renew.before_commit', 'renew.after_commit_before_response'))

    def test_C087_reclaim_crashes(self):
        self._lease_crashes('claim', ('claim.before_transaction', 'claim.after_generation_allocation', 'claim.after_insert',
                                     'claim.before_commit', 'claim.after_commit_before_response'), reclaim=True)

    def _ambiguous(self, call, *, committed):
        real = subject._commit
        def effect(c):
            if committed:
                real(c)
            raise subject._CommitUnknown('reviewed ambiguity')
        with mock.patch.object(subject, '_commit', side_effect=effect):
            self.assertEqual(call().outcome, 'commit_unknown')

    def test_C088_claim_did_commit(self):
        self._setup(count=2)
        self._ambiguous(lambda: self.facade.claim(token(1)), committed=True)
        history = self._other().query(token(1))
        self.assertEqual(history.outcome, 'claim_history')
        self.assertTrue(history.history_only)
        original = history.claim
        self.assertEqual(self._unchanged(lambda: self.facade.claim(token(1)), 'existing_claim_history').claim, original)
        self.clock.value += D
        self._ambiguous(lambda: self.facade.claim(token(2)), committed=True)
        self.assertEqual(self.facade.query(token(2)).claim.lease_generation, 2)

    def test_C089_claim_did_not_commit(self):
        self._setup()
        self._ambiguous(lambda: self.facade.claim(token(1)), committed=False)
        self.assertEqual(self._counts(), (0, 0))
        self.assertEqual(self._claim().lease_generation, 1)
        self.clock.value += D
        self._ambiguous(lambda: self.facade.claim(token(2)), committed=False)
        self.assertEqual(self._counts(), (1, 0))
        self.assertEqual(self._claim(2).lease_generation, 2)

    def test_C090_renewal_did_commit(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._ambiguous(lambda: self._renew(claim), committed=True)
        original = self.facade.query(claim.claim_id).renewals[0]
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self._unchanged(lambda: self._renew(claim), 'existing_renewal_history').renewal, original)

    def test_C091_renewal_did_not_commit(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._ambiguous(lambda: self._renew(claim), committed=False)
        self.assertEqual(self._counts(), (1, 0))
        self.clock.value = T + D
        self.assertEqual(self._renew(claim).outcome, 'expired_claim')
        self._claim(3, self._other())
        self._unchanged(lambda: self._renew(claim), 'stale_generation')
        self._revoke()
        self._unchanged(lambda: self._renew(claim), 'stale_generation')
        # Independent uncommitted request observes revocation on highest Claim.
        config = fixture.config_for(self.root / 'uncommitted-revoked.sqlite3')
        self.clock.value = T
        self._setup(configuration=config)
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self._ambiguous(lambda: self._renew(claim), committed=False)
        self._revoke()
        self.assertEqual(self._renew(claim).outcome, 'revoked')
        self.assertEqual(self._counts(config), (1, 0))

    def test_C092_writer_death(self):
        self._setup()
        before = _snapshot(self.configuration.database_path)
        self._child(self.configuration, 'held')
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self._claim()

    def test_C093_checkpoint(self):
        self._setup()
        claim = self._claim()
        for i in range(2, 5):
            self.clock.value += timedelta(seconds=1)
            self._renew(claim, i)
        before = _snapshot(self.configuration.database_path)
        with closing(outbox._connect(self.configuration.database_path)) as c:
            c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        reopened = self._facade(self._open())
        self.assertEqual(len(reopened.query(claim.claim_id).renewals), 3)
        self.assertEqual(_snapshot(self.configuration.database_path), before)
        self._child(self.configuration, 'history')
        self.clock.value = T + D + timedelta(seconds=3)
        self.assertEqual(self._claim(5, reopened).lease_generation, 2)

    def test_C094_reconciliation_fail_closed(self):
        self._setup()
        self.assertEqual(self.facade.query(token(1)).outcome, 'claim_not_found')
        claim = self._claim()
        other = self._other()
        self.assertEqual(other.query(claim.claim_id).outcome, 'claim_history')
        self.assertEqual(other.claim(claim.claim_id).outcome, 'claim_identity_conflict')
        self._corrupt(lambda c: c.execute(f'UPDATE {CLAIMS} SET lease_generation=3'))
        self.assertEqual(other.query(claim.claim_id).outcome, 'integrity_failure')

    def test_C095_canonical_loss(self):
        harness, facade = self._canonical()
        session = facade._session
        session.close()
        self.assertEqual(facade.claim(token(1)).outcome, 'ownership_lost')
        harness, facade = self._canonical()
        store = facade._store
        def fault(point):
            if point == 'claim.after_commit_before_response':
                facade._session._state = 'lost'
                raise integrated.windows_owner.AuthorizationDomainOwnershipIntegrityError('lost after commit')
        with mock.patch.object(store, '_fault', side_effect=fault):
            self.assertIn(facade.claim(token(2)).outcome, ('ownership_lost', 'commit_unknown'))
        with closing(outbox._connect(store.configuration.database_path)) as c:
            self.assertEqual(c.execute(f'SELECT count(*) FROM {CLAIMS}').fetchone()[0], 1)

    def test_C096_restart_no_restoration(self):
        self._setup()
        self._child(self.configuration, 'claim', 'claim.after_commit_before_response')
        old = self.facade.query(token(1)).claim
        self.assertNotEqual(old.executor_instance_id, self.facade.executor_instance_id)
        self.assertTrue(self.facade.query(token(1)).history_only)
        self._unchanged(lambda: self._renew(old, 2), 'claim_identity_conflict')
        self.clock.value += D
        self.assertEqual(self._claim(3).lease_generation, 2)
        harness, original = self._canonical()
        old = original.claim(token(1)).claim
        harness.restart()
        new = adapter._create_owned_dispatch_claim_lease(harness.coordinator._session)
        self.assertNotEqual(new.executor_instance_id, old.executor_instance_id)
        self.assertEqual(new.query(token(1)).claim, old)
        self.assertEqual(new.renew(token(2), old.identity, old.claim_id, 1).outcome, 'claim_identity_conflict')
        harness.clock.value += D
        self.assertEqual(new.claim(token(3)).claim.lease_generation, 2)

    def test_C097_two_claimants(self):
        harness, facade = self._canonical()
        other = adapter._create_owned_dispatch_claim_lease(facade._session)
        results = self._race(lambda: facade.claim(token(1)), lambda: other.claim(token(2)))
        self.assertEqual(sorted(r.outcome for r in results), ['newly_claimed', 'temporarily_unavailable'])
        self.assertEqual(self._counts(facade._store.configuration), (1, 0))
        for first_worker in (0, 1):
            harness.close()
            harness, left = self._canonical()
            right = adapter._create_owned_dispatch_claim_lease(left._session)
            workers = (left, right)
            self.assertEqual(workers[first_worker].claim(token(first_worker + 1)).outcome, 'newly_claimed')
            self.assertEqual(workers[1 - first_worker].claim(token(2 - first_worker)).outcome, 'temporarily_unavailable')
            self.assertEqual(self._counts(left._store.configuration), (1, 0))

    def test_C098_claim_renew_orders(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self._renew(claim).outcome, 'newly_renewed')
        self.assertEqual(self._other().claim(token(3)).outcome, 'temporarily_unavailable')
        self.clock.value = T + D + timedelta(seconds=1)
        owner = self._other()
        new = self._claim(3, owner)
        self._unchanged(lambda: self._renew(claim, 4), 'stale_generation')
        self.assertEqual(new.lease_generation, 2)
        # Opposite live writer order: failed Claim then successful Renewal.
        self.clock.value += timedelta(seconds=1)
        self.assertEqual(self.facade.claim(token(5)).outcome, 'temporarily_unavailable')
        self.assertEqual(self._renew(new, 5, owner).outcome, 'newly_renewed')

    def test_C099_expiry_orders(self):
        self._setup()
        claim = self._claim()
        self.clock.value = T + D - timedelta(microseconds=1)
        self.assertEqual(self._renew(claim).outcome, 'newly_renewed')
        self.clock.value = T + D
        self.assertEqual(self._other().claim(token(3)).outcome, 'temporarily_unavailable')
        self.clock.value = T + 2 * D - timedelta(microseconds=1)
        self._claim(3, self._other())
        self.assertEqual(self._renew(claim, 4).outcome, 'stale_generation')
        config = fixture.config_for(self.root / 'expiry-opposite.sqlite3')
        self.clock.value = T
        self._setup(configuration=config)
        old = self._claim()
        self.clock.value += D
        self._claim(2, self._other())
        self.assertEqual(self._renew(old, 3).outcome, 'stale_generation')
        self.assertEqual(self._counts(config), (2, 0))

    def test_C100_two_reclaimers(self):
        harness, facade = self._canonical()
        self.assertEqual(facade.claim(token(1)).outcome, 'newly_claimed')
        harness.clock.value += D
        left = adapter._create_owned_dispatch_claim_lease(facade._session)
        right = adapter._create_owned_dispatch_claim_lease(facade._session)
        results = self._race(lambda: left.claim(token(2)), lambda: right.claim(token(3)))
        self.assertEqual(sorted(r.outcome for r in results), ['newly_claimed', 'temporarily_unavailable'])
        self.assertEqual(next(r.claim.lease_generation for r in results if r.claim), 2)
        self.assertEqual(self._counts(facade._store.configuration), (2, 0))
        for first_worker in (0, 1):
            harness.close()
            harness, left = self._canonical()
            old = left.claim(token(1)).claim
            harness.clock.value += D
            right = adapter._create_owned_dispatch_claim_lease(left._session)
            workers = (left, right)
            result = workers[first_worker].claim(token(first_worker + 2))
            self.assertEqual(result.outcome, 'newly_claimed')
            self.assertEqual(result.claim.lease_generation, old.lease_generation + 1)
            self.assertEqual(workers[1 - first_worker].claim(token(3 - first_worker)).outcome, 'temporarily_unavailable')
            self.assertEqual(self._counts(left._store.configuration), (2, 0))

    def test_C101_retry_fresh_races(self):
        self._setup()
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        results = self._race(lambda: self.facade.claim(token(1)), lambda: self._renew(claim))
        self.assertEqual(sorted(r.outcome for r in results), ['existing_claim_history', 'newly_renewed'])
        self.clock.value = T + D + timedelta(seconds=1)
        results = self._race(lambda: self._renew(claim), lambda: self._other().claim(token(3)))
        self.assertEqual(sorted(r.outcome for r in results), ['existing_renewal_history', 'newly_claimed'])
        for reverse in (False, True):
            config = fixture.config_for(self.root / ('retry-orders-' + str(reverse) + '.sqlite3'))
            self.clock.value = T
            self._setup(count=2, configuration=config)
            old = self._claim()
            calls = [lambda: self.facade.claim(token(1)), lambda: self.facade.claim(token(2))]
            results = [call() for call in (reversed(calls) if reverse else calls)]
            self.assertEqual(sorted(r.outcome for r in results), ['existing_claim_history', 'newly_claimed'])
            self.clock.value += timedelta(seconds=1)
            calls = [lambda: self.facade.claim(token(1)), lambda: self._renew(old, 3)]
            results = [call() for call in (reversed(calls) if reverse else calls)]
            self.assertEqual(sorted(r.outcome for r in results), ['existing_claim_history', 'newly_renewed'])
            self.clock.value += D
            calls = [lambda: self._renew(old, 3), lambda: self._other().claim(token(4))]
            results = [call() for call in (reversed(calls) if reverse else calls)]
            self.assertEqual(sorted(r.outcome for r in results), ['existing_renewal_history', 'newly_claimed'])
            self.assertEqual(self._counts(config), (3, 1))

    def test_C102_identical_races(self):
        self._setup()
        results = self._race(lambda: self.facade.claim(token(1)), lambda: self.facade.claim(token(1)))
        self.assertEqual(sorted(r.outcome for r in results), ['existing_claim_history', 'newly_claimed'])
        claim = next(r.claim for r in results if r.claim)
        self.clock.value += timedelta(seconds=1)
        results = self._race(lambda: self._renew(claim), lambda: self._renew(claim))
        self.assertEqual(sorted(r.outcome for r in results), ['existing_renewal_history', 'newly_renewed'])
        self.assertEqual(self._counts(), (1, 1))

    def test_C103_busy(self):
        self._setup()
        def fault(point):
            if point == 'claim.before_transaction':
                raise sqlite3.OperationalError('database is locked')
        with mock.patch.object(self.store, '_fault', side_effect=fault):
            self.assertEqual(self.facade.claim(token(1)).outcome, 'storage_busy')
        original = self.store.configuration
        self.store.configuration = replace(original, busy_timeout_ms=1)
        with closing(outbox._connect(original.database_path)) as c:
            c.execute('BEGIN IMMEDIATE')
            self.assertEqual(self.facade.claim(token(1)).outcome, 'storage_busy')
            c.execute('ROLLBACK')
        self.store.configuration = original
        claim = self._claim()
        self.clock.value += timedelta(seconds=1)
        def unavailable(point):
            if point == 'renew.before_transaction':
                raise OSError('disposable storage unavailable')
        with mock.patch.object(self.store, '_fault', side_effect=unavailable):
            self.assertEqual(self._renew(claim).outcome, 'storage_unavailable')
        self.assertEqual(self._counts(), (1, 0))
        self.assertEqual(self._renew(claim).outcome, 'newly_renewed')

    def test_C104_many_raw_process_intents(self):
        self._setup(count=5)
        outputs = self._race(lambda: self._child(self.configuration, 'claim', attempt=1),
                             lambda: self._child(self.configuration, 'claim', attempt=2))
        self.assertTrue(all(json.loads(output)['outcome'] == 'newly_claimed' for output in outputs))
        for n in range(3, 6):
            result = json.loads(self._child(self.configuration, 'claim', attempt=n))
            self.assertEqual(result['outcome'], 'newly_claimed')
        self.assertEqual(self._counts(), (5, 0))
        with closing(outbox._connect(self.configuration.database_path)) as c:
            identities = [tuple(r) for r in c.execute(f'SELECT authorization_domain_id,issuer_kind,issuer_id,grant_id FROM {CLAIMS} ORDER BY grant_id')]
            self.assertEqual(identities, sorted(subject._grant_identity(g) for g in self.grants))
        self._predecessor('test_O45_concurrent_identical_admission_writers')

    def test_C105_canonical_operation_scope(self):
        harness, facade = self._canonical()
        observations = []
        original = facade._store._claim_dispatch_intent
        def wrapped(request):
            observations.append(facade._session._thread_operations.get(threading.get_ident(), 0))
            return original(request)
        with mock.patch.object(facade._store, '_claim_dispatch_intent', side_effect=wrapped):
            self.assertEqual(facade.claim(token(1)).outcome, 'newly_claimed')
        self.assertGreater(observations[0], 0)
        self.assertEqual(facade._session._thread_operations, {})
        second = adapter._create_owned_dispatch_claim_lease(facade._session)
        outcomes = self._race(lambda: facade.query(token(1)), lambda: second.query(token(1)))
        self.assertEqual([r.outcome for r in outcomes], ['claim_history', 'claim_history'])
        observed = []
        checked = adapter._checked_result
        def check(result, request):
            observed.append(facade._session._thread_operations.get(threading.get_ident(), 0))
            return checked(result, request)
        with mock.patch.object(adapter, '_checked_result', side_effect=check):
            self.assertEqual(facade.query(token(1)).outcome, 'claim_history')
        self.assertGreater(observed[0], 0)
        self._predecessor('test_O51_ownership_loss_around_commit')
        self._owner_predecessor('test_close_waits_for_active_operation_and_rejects_new_work')

    def test_C106_capability_boundary(self):
        self._setup()
        for value in (self.facade, self.facade._executor):
            for call in (copy.copy, copy.deepcopy, pickle.dumps):
                with self.assertRaises(TypeError):
                    call(value)
        with self.assertRaises(TypeError):
            adapter._create_owned_dispatch_claim_lease(SimpleNamespace(operation=lambda: True))
        with mock.patch.object(adapter.os, 'getpid', return_value=os.getpid() + 1):
            self.assertEqual(self.facade.claim(token(1)).outcome, 'invalid_input')
        counterfeit = object.__new__(adapter._ExecutorCapability)
        with self.assertRaises((ValueError, AttributeError)):
            adapter._validate_executor(counterfeit, self.facade._session)
        with self.assertRaises(TypeError):
            self.facade._executor._executor_id = token(99)
        with self.assertRaises(ValueError):
            adapter._validate_executor(self.facade._executor, self._facade()._session)
        with self.assertRaises(TypeError):
            adapter._create_owned_dispatch_claim_lease(self.facade._session, executor_instance_id=self.facade.executor_instance_id)

    def test_C107_terminal_sessions(self):
        self._setup()
        for state in ('closed', 'lost', 'fencing', 'fenced'):
            facade = self._facade()
            facade._session._state = state
            self.assertEqual(facade.claim(token(1)).outcome, 'ownership_lost')
            with self.assertRaises(ValueError):
                adapter._validate_executor(facade._executor, facade._session)
        fresh = self._facade()
        self.assertNotEqual(fresh.executor_instance_id, self.facade.executor_instance_id)
        self.store.fence()
        self.assertEqual(fresh.claim(token(1)).outcome, 'ownership_lost')

    def test_C108_current_vs_history(self):
        self._setup()
        old = self._claim()
        self.assertEqual(self._current(old).outcome, 'current_claim')
        self.assertEqual(self._current(old, self._other()).outcome, 'claim_identity_conflict')
        self.clock.value += timedelta(seconds=1)
        renewal = self._renew(old, 3).renewal
        self.assertEqual(self._current(old).effective_lease_until, renewal.lease_until)
        self.clock.value += D
        self.assertEqual(self._current(old).outcome, 'expired_claim')
        other = self._other()
        new = self._claim(2, other)
        self.assertEqual(self._current(old).outcome, 'stale_generation')
        self.assertEqual(self._current(new, other).outcome, 'current_claim')
        self._revoke()
        self.assertEqual(self._current(new, other).outcome, 'revoked')
        self.assertTrue(other.query(old.claim_id).history_only)

    def test_C109_full_aio055_compatibility(self):
        names = [name for name in outbox.AtomicDurableDispatchOutboxTests.__dict__ if name.startswith('test_O')]
        self.assertEqual(len(names), 60)
        for name in names:
            with self.subTest(predecessor=name):
                self._predecessor(name)

    def test_C110_presentation_boundary(self):
        self._predecessor('test_O52_integrated_same_live_session_retry')
        self._predecessor('test_O53_integrated_presentation_lost_on_restart')

    def test_C111_declared_package_inputs(self):
        import tomllib
        data = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
        self.assertEqual(data['tool']['setuptools']['packages'],
                         ['engineering_orchestration', 'engineering_orchestration._schemas',
                          'engineering_orchestration._roles', 'engineering_orchestration._sqlite_admission_migrations'])
        self.assertEqual(data['tool']['setuptools']['package-data']['engineering_orchestration._sqlite_admission_migrations'], ['*.sql'])
        self.assertFalse(data['tool']['setuptools']['include-package-data'])
        self.assertEqual(len(subject._migration_bytes()), 3)
        self.assertNotIn('claim', ' '.join(data['tool']['setuptools']['package-data']['engineering_orchestration._schemas']))
        # Explicit P1 prerequisite, supplied only by the reviewed validation command.
        owned = Path(os.environ['AIO056_PACKAGE_EVIDENCE'])
        self.assertEqual(owned.resolve(), owned)
        self.assertEqual(owned.parent, PARENT)
        self.assertTrue(owned.name.startswith('aio-056-package-'))
        self.assertFalse(owned.is_symlink() or owned.is_junction())
        manifest = json.loads((owned / 'source-map.json').read_text())
        self.assertEqual((owned / '.aio056-owner').read_text(), manifest['nonce'])
        wheel = owned / 'wheel/ai_engineering_orchestra-0.1.0-py3-none-any.whl'
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            dist = 'ai_engineering_orchestra-0.1.0.dist-info/'
            extras = {dist + name for name in ('METADATA', 'WHEEL', 'entry_points.txt', 'top_level.txt', 'RECORD')}
            self.assertEqual(set(names), set(manifest['package']) | extras)
            for name, digest in manifest['package'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest, name)
            for relative, digest in manifest['inputs'].items():
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
            for _, name, digest, resource in subject._migration_bytes():
                self.assertEqual(archive.read('engineering_orchestration/_sqlite_admission_migrations/' + name), resource)
            self.assertTrue(all(not name.startswith(('experiments/', 'tests/', '.ai/')) for name in names))

    def test_C112_process_safety_and_no_invocation(self):
        self._child(self.configuration, 'timeout', timeout=2)
        self.assertTrue(PROCESS_EVIDENCE)
        self.assertTrue(all(closed and reaped for _, _, _, _, closed, reaped in PROCESS_EVIDENCE))
        tree = ast.parse((ROOT / 'engineering_orchestration/_local_dispatch_claim_lease.py').read_text(encoding='utf-8'))
        imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        self.assertEqual(imports, ['os', 'secrets', 'threading'])
        for name in ('invoke', 'launch', 'transport', 'result', 'schedule', 'execute'):
            self.assertFalse(hasattr(adapter._OwnedDispatchClaimLease, name))
