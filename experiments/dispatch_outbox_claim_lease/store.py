"""Private AIO-054 SQLite dispatch/claim/lease experiment.

This module is intentionally self-contained, stdlib-only, nonpackaged, and
noncanonical.  It models storage hypotheses only.  It performs no transport,
Tool invocation, repository-resource access, credential work, or Result work.

The public surface is deliberately small and test-oriented:

* :class:`StoreConfiguration` pins one disposable ledger and the exact profile.
* :class:`DispatchOutboxClaimLeaseStore` provisions/migrates and operates it.
* request/record dataclasses keep complete identities explicit.
* :func:`open_profiled_connection` supports raw spawned-process storage probes.
* ``fault_hook(point)`` exposes fixed transaction cut points without accepting
  fault instructions from request values.

Passing this experiment does not establish a production contract or canonical
AIO-049 integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Callable


MINIMUM_SQLITE_VERSION = (3, 37, 0)
BUSY_TIMEOUT_MS = 2_000
LEASE_DURATION_US = 30_000_000
MAX_SIGNED_64 = 9_223_372_036_854_775_807
MIN_SIGNED_64 = -9_223_372_036_854_775_808
APPLICATION_ID = 0x41494F54
STORE_ID = "aio054.private.dispatch_outbox_claim_lease.sqlite"
LEGACY_SCHEMA_VERSION = 1
CURRENT_SCHEMA_VERSION = 2
LEGACY_RESOURCE_NAME = "0001_private_legacy.sql"
CURRENT_RESOURCE_NAME = "schema.sql"

FAULT_POINTS = (
    "provision.before_transaction", "provision.after_begin", "provision.after_schema",
    "provision.before_commit", "provision.after_commit",
    "migration.before_transaction", "migration.after_begin", "migration.after_dirty",
    "migration.after_schema", "migration.after_legacy_population",
    "migration.after_clean_transition", "migration.before_commit",
    "migration.after_commit",
    "admission.before_transaction", "admission.after_begin",
    "admission.after_admission_insert", "admission.after_intent_insert",
    "admission.after_watermark", "admission.before_commit", "admission.after_commit",
    "legacy_admission.before_transaction", "legacy_admission.after_begin",
    "legacy_admission.after_admission_insert", "legacy_admission.after_watermark",
    "legacy_admission.before_commit", "legacy_admission.after_commit",
    "revocation.before_transaction", "revocation.after_begin",
    "revocation.after_insert", "revocation.before_commit", "revocation.after_commit",
    "claim.before_transaction", "claim.after_begin",
    "claim.after_invariant_validation", "claim.after_clock_sample",
    "claim.after_insert", "claim.after_watermark", "claim.before_commit",
    "claim.after_commit",
    "renewal.before_transaction", "renewal.after_begin",
    "renewal.after_invariant_validation", "renewal.after_clock_sample",
    "renewal.after_insert", "renewal.after_watermark", "renewal.before_commit",
    "renewal.after_commit",
    "assessment.before_transaction", "assessment.after_begin",
    "assessment.after_clock_sample", "assessment.after_watermark",
    "assessment.before_commit", "assessment.after_commit",
    "fence.before_update", "fence.after_update", "fence.before_commit",
    "fence.after_commit",
)

FaultHook = Callable[[str], None]
PostCheck = Callable[[], bool]


class ExperimentStoreError(RuntimeError):
    """Base error for the private experiment Store."""


class ConfigurationError(ExperimentStoreError):
    """The trusted experiment configuration is unsupported."""


class IncompatibleSchemaError(ExperimentStoreError):
    """The ledger is not the exact expected schema generation."""


class IntegrityFailure(ExperimentStoreError):
    """Stored schema, metadata, identity, or payload integrity failed."""


class ClockFailure(ExperimentStoreError):
    """The trusted clock was unavailable or noncanonical."""


class ClockRegression(ExperimentStoreError):
    """The trusted clock preceded the durable watermark."""


class CommitUnknownFault(ExperimentStoreError):
    """Fault hook signal for an intentionally ambiguous commit boundary."""


class InjectedFault(ExperimentStoreError):
    """Fault hook signal for a known precommit rollback cut."""


@dataclass(frozen=True)
class StoreConfiguration:
    database_path: Path
    authorization_domain_id: str
    ledger_instance_id: str
    domain_generation: int = 1
    lease_duration_us: int = LEASE_DURATION_US
    busy_timeout_ms: int = BUSY_TIMEOUT_MS


@dataclass(frozen=True)
class DispatchIdentity:
    authorization_domain_id: str
    issuer_kind: str
    issuer_id: str
    grant_id: str

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (
            self.authorization_domain_id,
            self.issuer_kind,
            self.issuer_id,
            self.grant_id,
        )


@dataclass(frozen=True)
class AdmissionRequest:
    authorization_domain_id: str
    issuer_kind: str
    issuer_id: str
    grant_id: str
    run_id: str
    grant_payload: bytes
    binding_payload: bytes
    issued_at: datetime
    expires_at: datetime

    @property
    def identity(self) -> DispatchIdentity:
        return DispatchIdentity(
            self.authorization_domain_id,
            self.issuer_kind,
            self.issuer_id,
            self.grant_id,
        )


@dataclass(frozen=True)
class ClaimRequest:
    claim_id: str
    executor_instance_id: str


@dataclass(frozen=True)
class RenewalRequest:
    identity: DispatchIdentity
    claim_id: str
    executor_instance_id: str
    lease_generation: int
    renewal_id: str


@dataclass(frozen=True)
class CurrentClaimRequest:
    identity: DispatchIdentity
    claim_id: str
    executor_instance_id: str
    lease_generation: int


@dataclass(frozen=True)
class AdmissionRecord:
    identity: DispatchIdentity
    run_id: str
    grant_payload: bytes
    binding_payload: bytes
    issued_at: str
    issued_at_key: int
    expires_at: str
    expires_at_key: int
    decision_time: str
    decision_time_key: int


@dataclass(frozen=True)
class IntentRecord:
    identity: DispatchIdentity
    run_id: str
    admission_decision_time: str
    admission_decision_time_key: int


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    identity: DispatchIdentity
    executor_instance_id: str
    lease_generation: int
    acquired_at: str
    acquired_at_key: int
    lease_until: str
    lease_until_key: int


@dataclass(frozen=True)
class RenewalRecord:
    renewal_id: str
    claim_id: str
    identity: DispatchIdentity
    executor_instance_id: str
    lease_generation: int
    renewal_sequence: int
    renewed_at: str
    renewed_at_key: int
    lease_until: str
    lease_until_key: int


@dataclass(frozen=True)
class CurrentClaimAssessment:
    status: str
    reason: str
    claim: ClaimRecord
    effective_lease_until: str
    effective_lease_until_key: int
    observed_at: str | None
    observed_at_key: int | None


@dataclass(frozen=True)
class ConnectionProfile:
    sqlite_version: str
    journal_mode: str
    synchronous: int
    foreign_keys: int
    locking_mode: str
    busy_timeout_ms: int
    isolation_level: None
    write_begin: str = "BEGIN IMMEDIATE"


@dataclass(frozen=True)
class OperationResult:
    outcome: str
    detail: str = ""
    retry: str = "none"
    admission: AdmissionRecord | None = None
    intent: IntentRecord | None = None
    claim: ClaimRecord | None = None
    renewal: RenewalRecord | None = None
    assessment: CurrentClaimAssessment | None = None
    exact_history: bool = False
    reevaluation: bool = False
    committed: bool | None = None
    profile: ConnectionProfile | None = None


_LEGACY_SCHEMA_SQL = r"""
CREATE TABLE experiment_metadata (
    singleton INTEGER NOT NULL PRIMARY KEY CHECK (singleton = 1),
    store_id TEXT NOT NULL CHECK (store_id <> ''),
    application_id INTEGER NOT NULL,
    authorization_domain_id BLOB NOT NULL UNIQUE
        CHECK (length(authorization_domain_id) > 0),
    schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
    schema_manifest_id TEXT NOT NULL CHECK (schema_manifest_id <> ''),
    schema_fingerprint TEXT NOT NULL CHECK (length(schema_fingerprint) = 64),
    ledger_instance_id BLOB NOT NULL CHECK (length(ledger_instance_id) > 0),
    domain_generation INTEGER NOT NULL CHECK (domain_generation > 0),
    activation_state TEXT NOT NULL
        CHECK (activation_state IN ('active', 'fenced')),
    migration_state TEXT NOT NULL
        CHECK (migration_state IN ('clean', 'dirty')),
    revocation_state_complete INTEGER NOT NULL
        CHECK (revocation_state_complete IN (0, 1)),
    last_decision_time TEXT,
    last_decision_time_key INTEGER,
    CHECK (
        (last_decision_time IS NULL AND last_decision_time_key IS NULL)
        OR
        (last_decision_time IS NOT NULL AND last_decision_time <> ''
         AND last_decision_time_key IS NOT NULL)
    )
) STRICT;

CREATE TABLE experiment_schema_migrations (
    migration_id INTEGER NOT NULL PRIMARY KEY,
    resource_name TEXT NOT NULL UNIQUE CHECK (resource_name <> ''),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE experiment_admissions (
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL CHECK (length(grant_id) > 0),
    run_id BLOB NOT NULL CHECK (length(run_id) > 0),
    grant_payload BLOB NOT NULL CHECK (length(grant_payload) > 0),
    binding_payload BLOB NOT NULL CHECK (length(binding_payload) > 0),
    issued_at TEXT NOT NULL CHECK (issued_at <> ''),
    issued_at_key INTEGER NOT NULL,
    expires_at TEXT NOT NULL CHECK (expires_at <> ''),
    expires_at_key INTEGER NOT NULL,
    decision_time TEXT NOT NULL CHECK (decision_time <> ''),
    decision_time_key INTEGER NOT NULL,
    admission_payload BLOB NOT NULL CHECK (length(admission_payload) > 0),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES experiment_metadata (authorization_domain_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (issued_at_key < expires_at_key)
) STRICT, WITHOUT ROWID;

CREATE UNIQUE INDEX experiment_admission_domain_run_unique
ON experiment_admissions (authorization_domain_id, run_id);

CREATE TABLE experiment_revocations (
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL CHECK (length(grant_id) > 0),
    run_id BLOB NOT NULL CHECK (length(run_id) > 0),
    grant_payload BLOB NOT NULL CHECK (length(grant_payload) > 0),
    revoked_at TEXT NOT NULL CHECK (revoked_at <> ''),
    revoked_at_key INTEGER NOT NULL,
    revocation_payload BLOB NOT NULL CHECK (length(revocation_payload) > 0),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES experiment_metadata (authorization_domain_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE TRIGGER experiment_metadata_insert_once
BEFORE INSERT ON experiment_metadata
WHEN EXISTS (SELECT 1 FROM experiment_metadata)
BEGIN
    SELECT RAISE(ABORT, 'Experiment metadata already exists');
END;

CREATE TRIGGER experiment_metadata_no_delete
BEFORE DELETE ON experiment_metadata
BEGIN
    SELECT RAISE(ABORT, 'Experiment metadata cannot be deleted');
END;

CREATE TRIGGER experiment_metadata_transition_guard
BEFORE UPDATE ON experiment_metadata
WHEN
    NEW.singleton IS NOT OLD.singleton
    OR NEW.store_id IS NOT OLD.store_id
    OR NEW.application_id IS NOT OLD.application_id
    OR NEW.authorization_domain_id IS NOT OLD.authorization_domain_id
    OR NEW.ledger_instance_id IS NOT OLD.ledger_instance_id
    OR NEW.domain_generation IS NOT OLD.domain_generation
    OR (OLD.activation_state = 'fenced' AND NEW.activation_state <> 'fenced')
    OR NEW.revocation_state_complete < OLD.revocation_state_complete
    OR NEW.schema_version < OLD.schema_version
    OR (
        (NEW.schema_version IS NOT OLD.schema_version
         OR NEW.schema_manifest_id IS NOT OLD.schema_manifest_id
         OR NEW.schema_fingerprint IS NOT OLD.schema_fingerprint)
        AND OLD.migration_state <> 'dirty'
    )
BEGIN
    SELECT RAISE(ABORT, 'Experiment metadata transition is prohibited');
END;

CREATE TRIGGER experiment_watermark_monotonic
BEFORE UPDATE ON experiment_metadata
WHEN
    (NEW.last_decision_time IS NULL) IS NOT
        (NEW.last_decision_time_key IS NULL)
    OR (OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key IS NULL)
    OR (OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key < OLD.last_decision_time_key)
    OR (OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key = OLD.last_decision_time_key
        AND NEW.last_decision_time IS NOT OLD.last_decision_time)
    OR (OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key > OLD.last_decision_time_key
        AND NEW.last_decision_time IS OLD.last_decision_time)
BEGIN
    SELECT RAISE(ABORT, 'Experiment watermark cannot regress or rebound');
END;

CREATE TRIGGER experiment_migrations_contiguous
BEFORE INSERT ON experiment_schema_migrations
WHEN NEW.migration_id <> COALESCE(
    (SELECT MAX(migration_id) + 1 FROM experiment_schema_migrations), 1
)
BEGIN
    SELECT RAISE(ABORT, 'Experiment migration history must be contiguous');
END;

CREATE TRIGGER experiment_migrations_no_update
BEFORE UPDATE ON experiment_schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'Experiment migration history is immutable');
END;

CREATE TRIGGER experiment_migrations_no_delete
BEFORE DELETE ON experiment_schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'Experiment migration history is immutable');
END;

CREATE TRIGGER experiment_admissions_no_update
BEFORE UPDATE ON experiment_admissions
BEGIN
    SELECT RAISE(ABORT, 'Experiment Admissions are immutable');
END;

CREATE TRIGGER experiment_admissions_no_delete
BEFORE DELETE ON experiment_admissions
BEGIN
    SELECT RAISE(ABORT, 'Experiment Admissions are immutable');
END;

CREATE TRIGGER experiment_admissions_no_revoked_insert
BEFORE INSERT ON experiment_admissions
WHEN EXISTS (
    SELECT 1 FROM experiment_revocations
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'A revoked Grant cannot be admitted');
END;

CREATE TRIGGER experiment_revocations_no_rebound
BEFORE INSERT ON experiment_revocations
WHEN EXISTS (
    SELECT 1 FROM experiment_admissions
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
      AND (run_id <> NEW.run_id OR grant_payload <> NEW.grant_payload)
)
BEGIN
    SELECT RAISE(ABORT, 'Grant identity cannot rebound across records');
END;

CREATE TRIGGER experiment_revocations_no_update
BEFORE UPDATE ON experiment_revocations
BEGIN
    SELECT RAISE(ABORT, 'Experiment revocations are immutable');
END;

CREATE TRIGGER experiment_revocations_no_delete
BEFORE DELETE ON experiment_revocations
BEGIN
    SELECT RAISE(ABORT, 'Experiment revocations are immutable');
END;
"""


# Kept byte-for-byte equivalent to schema.sql so operational code never reads
# repository resources.  Only the configured disposable SQLite ledger is
# touched at runtime.
CURRENT_SCHEMA_SQL = r"""-- AIO-054 private experiment schema extension (version 2).
--
-- This file is deliberately noncanonical and nonpackaged.  It is applied only
-- to a disposable version-1 experiment ledger by store.py while one
-- BEGIN EXCLUSIVE transaction is active.  The version-1 Admission,
-- revocation, metadata, and migration-history objects are created by the
-- private provisioning code in store.py.

CREATE TABLE dispatch_intents (
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL
        CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL
        CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL
        CHECK (length(grant_id) > 0),
    run_id BLOB NOT NULL
        CHECK (length(run_id) > 0),
    admission_decision_time TEXT NOT NULL
        CHECK (admission_decision_time <> ''),
    admission_decision_time_key INTEGER NOT NULL,
    intent_payload BLOB NOT NULL
        CHECK (length(intent_payload) > 0),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) REFERENCES experiment_admissions (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE TABLE legacy_admission_markers (
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL
        CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL
        CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL
        CHECK (length(grant_id) > 0),
    migration_id INTEGER NOT NULL
        CHECK (migration_id = 2),
    marker_payload BLOB NOT NULL
        CHECK (length(marker_payload) > 0),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) REFERENCES experiment_admissions (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE TABLE dispatch_claims (
    claim_id BLOB NOT NULL PRIMARY KEY
        CHECK (length(claim_id) > 0),
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL
        CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL
        CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL
        CHECK (length(grant_id) > 0),
    executor_instance_id BLOB NOT NULL
        CHECK (length(executor_instance_id) > 0),
    lease_generation INTEGER NOT NULL
        CHECK (lease_generation > 0),
    acquired_at TEXT NOT NULL
        CHECK (acquired_at <> ''),
    acquired_at_key INTEGER NOT NULL,
    lease_until TEXT NOT NULL
        CHECK (lease_until <> ''),
    lease_until_key INTEGER NOT NULL,
    claim_payload BLOB NOT NULL
        CHECK (length(claim_payload) > 0),
    UNIQUE (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id,
        lease_generation
    ),
    UNIQUE (
        claim_id,
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id,
        executor_instance_id,
        lease_generation
    ),
    FOREIGN KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) REFERENCES dispatch_intents (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (lease_until_key > acquired_at_key)
) STRICT, WITHOUT ROWID;

CREATE INDEX dispatch_claims_generation_order
ON dispatch_claims (
    authorization_domain_id,
    issuer_kind,
    issuer_id,
    grant_id,
    lease_generation DESC
);

CREATE TABLE lease_renewals (
    renewal_id BLOB NOT NULL PRIMARY KEY
        CHECK (length(renewal_id) > 0),
    claim_id BLOB NOT NULL
        CHECK (length(claim_id) > 0),
    authorization_domain_id BLOB NOT NULL
        CHECK (length(authorization_domain_id) > 0),
    issuer_kind BLOB NOT NULL
        CHECK (length(issuer_kind) > 0),
    issuer_id BLOB NOT NULL
        CHECK (length(issuer_id) > 0),
    grant_id BLOB NOT NULL
        CHECK (length(grant_id) > 0),
    executor_instance_id BLOB NOT NULL
        CHECK (length(executor_instance_id) > 0),
    lease_generation INTEGER NOT NULL
        CHECK (lease_generation > 0),
    renewal_sequence INTEGER NOT NULL
        CHECK (renewal_sequence > 0),
    renewed_at TEXT NOT NULL
        CHECK (renewed_at <> ''),
    renewed_at_key INTEGER NOT NULL,
    lease_until TEXT NOT NULL
        CHECK (lease_until <> ''),
    lease_until_key INTEGER NOT NULL,
    renewal_payload BLOB NOT NULL
        CHECK (length(renewal_payload) > 0),
    UNIQUE (claim_id, renewal_sequence),
    FOREIGN KEY (
        claim_id,
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id,
        executor_instance_id,
        lease_generation
    ) REFERENCES dispatch_claims (
        claim_id,
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id,
        executor_instance_id,
        lease_generation
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (lease_until_key > renewed_at_key)
) STRICT, WITHOUT ROWID;

CREATE INDEX lease_renewals_claim_sequence
ON lease_renewals (claim_id, renewal_sequence);

CREATE TRIGGER dispatch_intents_no_legacy_overlap
BEFORE INSERT ON dispatch_intents
WHEN EXISTS (
    SELECT 1
    FROM legacy_admission_markers
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intent overlaps a legacy marker');
END;

CREATE TRIGGER legacy_admission_markers_no_intent_overlap
BEFORE INSERT ON legacy_admission_markers
WHEN EXISTS (
    SELECT 1
    FROM dispatch_intents
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Legacy marker overlaps a Dispatch Intent');
END;

CREATE TRIGGER dispatch_intents_no_update
BEFORE UPDATE ON dispatch_intents
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intents are immutable');
END;

CREATE TRIGGER dispatch_intents_no_delete
BEFORE DELETE ON dispatch_intents
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intents are immutable');
END;

CREATE TRIGGER legacy_admission_markers_no_update
BEFORE UPDATE ON legacy_admission_markers
BEGIN
    SELECT RAISE(ABORT, 'Legacy Admission markers are immutable');
END;

CREATE TRIGGER legacy_admission_markers_no_delete
BEFORE DELETE ON legacy_admission_markers
BEGIN
    SELECT RAISE(ABORT, 'Legacy Admission markers are immutable');
END;

CREATE TRIGGER dispatch_claims_no_update
BEFORE UPDATE ON dispatch_claims
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Claims are append-only');
END;

CREATE TRIGGER dispatch_claims_no_delete
BEFORE DELETE ON dispatch_claims
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Claims are append-only');
END;

CREATE TRIGGER lease_renewals_no_update
BEFORE UPDATE ON lease_renewals
BEGIN
    SELECT RAISE(ABORT, 'Lease Renewals are append-only');
END;

CREATE TRIGGER lease_renewals_no_delete
BEFORE DELETE ON lease_renewals
BEGIN
    SELECT RAISE(ABORT, 'Lease Renewals are append-only');
END;
"""


_REFERENCE_FINGERPRINTS: dict[int, str] = {}


def _result(outcome: str, detail: str = "", **values: object) -> OperationResult:
    return OperationResult(outcome=outcome, detail=detail, **values)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _text_bytes(value: object, name: str) -> bytes:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a nonempty exact string")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} is not canonical UTF-8") from error
    if not encoded:
        raise ValueError(f"{name} must not encode to empty bytes")
    return encoded


def _decode_text(value: object, name: str) -> str:
    if type(value) is not bytes or not value:
        raise IntegrityFailure(f"stored {name} is not nonempty bytes")
    try:
        decoded = value.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise IntegrityFailure(f"stored {name} is not canonical UTF-8") from error
    if decoded.encode("utf-8") != value:
        raise IntegrityFailure(f"stored {name} does not round-trip as UTF-8")
    return decoded


def _require_payload(value: object, name: str) -> bytes:
    if type(value) is not bytes or not value:
        raise ValueError(f"{name} must be nonempty exact bytes")
    return value


def _identity_bytes(identity: DispatchIdentity) -> tuple[bytes, bytes, bytes, bytes]:
    if type(identity) is not DispatchIdentity:
        raise ValueError("identity must be the exact DispatchIdentity type")
    return tuple(
        _text_bytes(value, name)
        for value, name in zip(
            identity.as_tuple(),
            ("authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"),
            strict=True,
        )
    )


def _identity_from_row(row: sqlite3.Row) -> DispatchIdentity:
    return DispatchIdentity(
        _decode_text(row["authorization_domain_id"], "authorization_domain_id"),
        _decode_text(row["issuer_kind"], "issuer_kind"),
        _decode_text(row["issuer_id"], "issuer_id"),
        _decode_text(row["grant_id"], "grant_id"),
    )


def _canonical_time(value: object) -> tuple[datetime, str, int]:
    if type(value) is not datetime:
        raise ValueError("time must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("time must be UTC-aware with zero offset")
    utc_value = value.astimezone(timezone.utc)
    text = (
        f"{utc_value.year:04d}-{utc_value.month:02d}-{utc_value.day:02d}T"
        f"{utc_value.hour:02d}:{utc_value.minute:02d}:{utc_value.second:02d}."
        f"{utc_value.microsecond:06d}Z"
    )
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = utc_value - epoch
    key = (
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )
    if key < MIN_SIGNED_64 or key > MAX_SIGNED_64:
        raise ValueError("time key is outside signed 64-bit range")
    return utc_value, text, key


def _parse_time(text: object, key: object) -> datetime:
    if type(text) is not str or len(text) != 27 or not text.endswith("Z"):
        raise IntegrityFailure("stored timestamp is not canonical")
    if type(key) is not int or key < MIN_SIGNED_64 or key > MAX_SIGNED_64:
        raise IntegrityFailure("stored timestamp key is invalid")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
        _, canonical, parsed_key = _canonical_time(parsed)
    except (TypeError, ValueError, OverflowError) as error:
        raise IntegrityFailure("stored timestamp cannot be parsed") from error
    if canonical != text or parsed_key != key:
        raise IntegrityFailure("stored timestamp text/key disagree")
    return parsed


def _time_from_key(key: int) -> tuple[datetime, str, int]:
    if type(key) is not int or key < MIN_SIGNED_64 or key > MAX_SIGNED_64:
        raise ValueError("computed timestamp key is outside signed 64-bit range")
    try:
        value = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
            microseconds=key
        )
    except (OverflowError, ValueError) as error:
        raise ValueError("computed timestamp is outside datetime range") from error
    return _canonical_time(value)


def _schema_bytes() -> bytes:
    data = CURRENT_SCHEMA_SQL.encode("utf-8")
    if not data or b"\r" in data:
        raise IncompatibleSchemaError("embedded schema must be canonical UTF-8/LF")
    return data


def _statements(sql: str) -> tuple[str, ...]:
    statements: list[str] = []
    pending = ""
    for line in sql.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            if statement:
                statements.append(statement)
            pending = ""
    if pending.strip():
        raise IncompatibleSchemaError("schema contains an incomplete SQL statement")
    return tuple(statements)


def _apply_statements(connection: sqlite3.Connection, sql: str) -> None:
    for statement in _statements(sql):
        connection.execute(statement)


def _schema_fingerprint(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type COLLATE BINARY, name COLLATE BINARY
        """
    ).fetchall()
    material = _canonical_json(
        [[row["type"], row["name"], row["tbl_name"], row["sql"]] for row in rows]
    )
    return hashlib.sha256(material).hexdigest()


def _reference_fingerprint(version: int) -> str:
    cached = _REFERENCE_FINGERPRINTS.get(version)
    if cached is not None:
        return cached
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        _apply_statements(connection, _LEGACY_SCHEMA_SQL)
        if version == CURRENT_SCHEMA_VERSION:
            _apply_statements(connection, _schema_bytes().decode("utf-8"))
        elif version != LEGACY_SCHEMA_VERSION:
            raise ValueError("unsupported reference schema version")
        fingerprint = _schema_fingerprint(connection)
    finally:
        connection.close()
    _REFERENCE_FINGERPRINTS[version] = fingerprint
    return fingerprint


def _migration_entries(version: int) -> tuple[tuple[int, str, str], ...]:
    legacy_hash = hashlib.sha256(_LEGACY_SCHEMA_SQL.encode("utf-8")).hexdigest()
    entries = [(LEGACY_SCHEMA_VERSION, LEGACY_RESOURCE_NAME, legacy_hash)]
    if version == CURRENT_SCHEMA_VERSION:
        entries.append(
            (
                CURRENT_SCHEMA_VERSION,
                CURRENT_RESOURCE_NAME,
                hashlib.sha256(_schema_bytes()).hexdigest(),
            )
        )
    elif version != LEGACY_SCHEMA_VERSION:
        raise ValueError("unsupported migration manifest version")
    return tuple(entries)


def _manifest_id(version: int) -> str:
    material = "\n".join(
        f"{migration_id}:{name}:{digest}"
        for migration_id, name, digest in _migration_entries(version)
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _validate_configuration(configuration: object, *, require_file: bool) -> StoreConfiguration:
    if type(configuration) is not StoreConfiguration:
        raise ConfigurationError("configuration must be the exact StoreConfiguration type")
    if (
        type(configuration.lease_duration_us) is not int
        or configuration.lease_duration_us != LEASE_DURATION_US
    ):
        raise ConfigurationError("lease_duration_us must be exactly 30_000_000")
    if (
        type(configuration.busy_timeout_ms) is not int
        or configuration.busy_timeout_ms != BUSY_TIMEOUT_MS
    ):
        raise ConfigurationError("busy_timeout_ms must be exactly 2000")
    _text_bytes(configuration.authorization_domain_id, "authorization_domain_id")
    _text_bytes(configuration.ledger_instance_id, "ledger_instance_id")
    if (
        type(configuration.domain_generation) is not int
        or configuration.domain_generation <= 0
        or configuration.domain_generation > MAX_SIGNED_64
    ):
        raise ConfigurationError("domain_generation must be a positive signed-64 integer")
    if sqlite3.sqlite_version_info < MINIMUM_SQLITE_VERSION:
        raise ConfigurationError("SQLite 3.37.0 or newer is required")
    path = configuration.database_path
    if not isinstance(path, Path) or not path.is_absolute():
        raise ConfigurationError("database_path must be an absolute pathlib.Path")
    raw = str(path)
    if raw.startswith("\\\\") or raw.startswith("//"):
        raise ConfigurationError("UNC and network-share paths are unsupported")
    try:
        resolved_parent = path.parent.resolve(strict=True)
    except OSError as error:
        raise ConfigurationError("database parent must already exist") from error
    if not resolved_parent.is_dir():
        raise ConfigurationError("database parent must be a directory")
    for component in (path.parent, *path.parent.parents):
        is_junction = getattr(component, "is_junction", lambda: False)
        if component.is_symlink() or is_junction():
            raise ConfigurationError("symlink and junction path aliases are unsupported")
    if require_file:
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ConfigurationError("configured experiment ledger does not exist") from error
        is_junction = getattr(path, "is_junction", lambda: False)
        if not resolved.is_file() or path.is_symlink() or is_junction():
            raise ConfigurationError("configured experiment ledger is not a regular local file")
    return configuration


def _connection_profile(connection: sqlite3.Connection) -> ConnectionProfile:
    return ConnectionProfile(
        sqlite_version=sqlite3.sqlite_version,
        journal_mode=str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower(),
        synchronous=int(connection.execute("PRAGMA synchronous").fetchone()[0]),
        foreign_keys=int(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
        locking_mode=str(connection.execute("PRAGMA locking_mode").fetchone()[0]).lower(),
        busy_timeout_ms=int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
        isolation_level=None,
    )


def _configure_connection(
    connection: sqlite3.Connection,
    configuration: StoreConfiguration,
    *,
    establish_wal: bool,
) -> ConnectionProfile:
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA locking_mode=NORMAL")
    if establish_wal:
        row = connection.execute("PRAGMA journal_mode=WAL").fetchone()
        if row is None or str(row[0]).lower() != "wal":
            raise ConfigurationError("WAL mode could not be established")
    connection.execute("PRAGMA synchronous=FULL")
    profile = _connection_profile(connection)
    if (
        profile.journal_mode != "wal"
        or profile.synchronous != 2
        or profile.foreign_keys != 1
        or profile.locking_mode != "normal"
        or profile.busy_timeout_ms != BUSY_TIMEOUT_MS
        or connection.isolation_level is not None
    ):
        raise ConfigurationError("required WAL/FULL/FK/NORMAL/2000/autocommit profile is absent")
    return profile


def open_profiled_connection(
    configuration: StoreConfiguration,
    *,
    establish_wal: bool = False,
) -> sqlite3.Connection:
    """Open the exact pinned file for private raw storage-mechanism probes."""

    config = _validate_configuration(configuration, require_file=True)
    connection = sqlite3.connect(
        config.database_path.as_uri() + "?mode=rw",
        uri=True,
        timeout=BUSY_TIMEOUT_MS / 1_000,
        isolation_level=None,
    )
    try:
        _configure_connection(connection, config, establish_wal=establish_wal)
    except BaseException:
        connection.close()
        raise
    return connection


def _safe_rollback(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _is_busy(error: BaseException) -> bool:
    code = getattr(error, "sqlite_errorcode", None)
    return code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED} or any(
        marker in str(error).lower() for marker in ("busy", "locked")
    )


def _fault(hook: FaultHook | None, point: str) -> None:
    if hook is not None:
        hook(point)


def _post_check(check: PostCheck | None) -> bool:
    return True if check is None else check() is True


__all__ = (
    "APPLICATION_ID",
    "BUSY_TIMEOUT_MS",
    "CURRENT_SCHEMA_VERSION",
    "CURRENT_SCHEMA_SQL",
    "FAULT_POINTS",
    "LEASE_DURATION_US",
    "MINIMUM_SQLITE_VERSION",
    "AdmissionRecord",
    "AdmissionRequest",
    "ClaimRecord",
    "ClaimRequest",
    "ClockFailure",
    "ClockRegression",
    "CommitUnknownFault",
    "ConfigurationError",
    "ConnectionProfile",
    "CurrentClaimAssessment",
    "CurrentClaimRequest",
    "DispatchIdentity",
    "DispatchOutboxClaimLeaseStore",
    "ExperimentStoreError",
    "InjectedFault",
    "IntegrityFailure",
    "IntentRecord",
    "OperationResult",
    "RenewalRecord",
    "RenewalRequest",
    "StoreConfiguration",
    "open_profiled_connection",
)


@dataclass(frozen=True)
class _Metadata:
    activation_state: str
    revocation_state_complete: bool
    watermark_text: str | None
    watermark_key: int | None


def _admission_payload(
    request: AdmissionRequest,
    issued_text: str,
    issued_key: int,
    expires_text: str,
    expires_key: int,
    decision_text: str,
    decision_key: int,
) -> bytes:
    return _canonical_json(
        {
            "binding_payload_hex": request.binding_payload.hex(),
            "decision_time": decision_text,
            "decision_time_key": decision_key,
            "expires_at": expires_text,
            "expires_at_key": expires_key,
            "grant_payload_hex": request.grant_payload.hex(),
            "identity": list(request.identity.as_tuple()),
            "issued_at": issued_text,
            "issued_at_key": issued_key,
            "run_id": request.run_id,
        }
    )


def _intent_payload(record: IntentRecord) -> bytes:
    return _canonical_json(
        {
            "admission_decision_time": record.admission_decision_time,
            "admission_decision_time_key": record.admission_decision_time_key,
            "identity": list(record.identity.as_tuple()),
            "run_id": record.run_id,
        }
    )


def _marker_payload(identity: DispatchIdentity) -> bytes:
    return _canonical_json(
        {"identity": list(identity.as_tuple()), "migration_id": CURRENT_SCHEMA_VERSION}
    )


def _claim_payload(record: ClaimRecord) -> bytes:
    return _canonical_json(
        {
            "acquired_at": record.acquired_at,
            "acquired_at_key": record.acquired_at_key,
            "claim_id": record.claim_id,
            "executor_instance_id": record.executor_instance_id,
            "identity": list(record.identity.as_tuple()),
            "lease_generation": record.lease_generation,
            "lease_until": record.lease_until,
            "lease_until_key": record.lease_until_key,
        }
    )


def _renewal_payload(record: RenewalRecord) -> bytes:
    return _canonical_json(
        {
            "claim_id": record.claim_id,
            "executor_instance_id": record.executor_instance_id,
            "identity": list(record.identity.as_tuple()),
            "lease_generation": record.lease_generation,
            "lease_until": record.lease_until,
            "lease_until_key": record.lease_until_key,
            "renewal_id": record.renewal_id,
            "renewal_sequence": record.renewal_sequence,
            "renewed_at": record.renewed_at,
            "renewed_at_key": record.renewed_at_key,
        }
    )


def _revocation_payload(
    identity: DispatchIdentity,
    run_id: str,
    grant_payload: bytes,
    revoked_at: str,
    revoked_at_key: int,
) -> bytes:
    return _canonical_json(
        {
            "grant_payload_hex": grant_payload.hex(),
            "identity": list(identity.as_tuple()),
            "revoked_at": revoked_at,
            "revoked_at_key": revoked_at_key,
            "run_id": run_id,
        }
    )


def _admission_from_row(row: sqlite3.Row) -> AdmissionRecord:
    identity = _identity_from_row(row)
    run_id = _decode_text(row["run_id"], "run_id")
    grant_payload = bytes(row["grant_payload"])
    binding_payload = bytes(row["binding_payload"])
    if not grant_payload or not binding_payload:
        raise IntegrityFailure("stored Admission payload components are empty")
    _parse_time(row["issued_at"], row["issued_at_key"])
    _parse_time(row["expires_at"], row["expires_at_key"])
    _parse_time(row["decision_time"], row["decision_time_key"])
    record = AdmissionRecord(
        identity=identity,
        run_id=run_id,
        grant_payload=grant_payload,
        binding_payload=binding_payload,
        issued_at=row["issued_at"],
        issued_at_key=row["issued_at_key"],
        expires_at=row["expires_at"],
        expires_at_key=row["expires_at_key"],
        decision_time=row["decision_time"],
        decision_time_key=row["decision_time_key"],
    )
    expected = _canonical_json(
        {
            "binding_payload_hex": binding_payload.hex(),
            "decision_time": record.decision_time,
            "decision_time_key": record.decision_time_key,
            "expires_at": record.expires_at,
            "expires_at_key": record.expires_at_key,
            "grant_payload_hex": grant_payload.hex(),
            "identity": list(identity.as_tuple()),
            "issued_at": record.issued_at,
            "issued_at_key": record.issued_at_key,
            "run_id": run_id,
        }
    )
    if bytes(row["admission_payload"]) != expected:
        raise IntegrityFailure("stored Admission payload/index values disagree")
    if record.issued_at_key >= record.expires_at_key:
        raise IntegrityFailure("stored Admission authority interval is invalid")
    return record


def _intent_from_row(row: sqlite3.Row) -> IntentRecord:
    record = IntentRecord(
        identity=_identity_from_row(row),
        run_id=_decode_text(row["run_id"], "run_id"),
        admission_decision_time=row["admission_decision_time"],
        admission_decision_time_key=row["admission_decision_time_key"],
    )
    _parse_time(record.admission_decision_time, record.admission_decision_time_key)
    if bytes(row["intent_payload"]) != _intent_payload(record):
        raise IntegrityFailure("stored Intent payload/index values disagree")
    return record


def _claim_from_row(row: sqlite3.Row) -> ClaimRecord:
    record = ClaimRecord(
        claim_id=_decode_text(row["claim_id"], "claim_id"),
        identity=_identity_from_row(row),
        executor_instance_id=_decode_text(
            row["executor_instance_id"], "executor_instance_id"
        ),
        lease_generation=row["lease_generation"],
        acquired_at=row["acquired_at"],
        acquired_at_key=row["acquired_at_key"],
        lease_until=row["lease_until"],
        lease_until_key=row["lease_until_key"],
    )
    _parse_time(record.acquired_at, record.acquired_at_key)
    _parse_time(record.lease_until, record.lease_until_key)
    if (
        type(record.lease_generation) is not int
        or record.lease_generation <= 0
        or record.lease_generation > MAX_SIGNED_64
        or record.lease_until_key - record.acquired_at_key != LEASE_DURATION_US
        or bytes(row["claim_payload"]) != _claim_payload(record)
    ):
        raise IntegrityFailure("stored Claim payload, generation, or Lease disagrees")
    return record


def _renewal_from_row(row: sqlite3.Row) -> RenewalRecord:
    record = RenewalRecord(
        renewal_id=_decode_text(row["renewal_id"], "renewal_id"),
        claim_id=_decode_text(row["claim_id"], "claim_id"),
        identity=_identity_from_row(row),
        executor_instance_id=_decode_text(
            row["executor_instance_id"], "executor_instance_id"
        ),
        lease_generation=row["lease_generation"],
        renewal_sequence=row["renewal_sequence"],
        renewed_at=row["renewed_at"],
        renewed_at_key=row["renewed_at_key"],
        lease_until=row["lease_until"],
        lease_until_key=row["lease_until_key"],
    )
    _parse_time(record.renewed_at, record.renewed_at_key)
    _parse_time(record.lease_until, record.lease_until_key)
    if (
        type(record.lease_generation) is not int
        or record.lease_generation <= 0
        or record.lease_generation > MAX_SIGNED_64
        or type(record.renewal_sequence) is not int
        or record.renewal_sequence <= 0
        or record.renewal_sequence > MAX_SIGNED_64
        or record.lease_until_key - record.renewed_at_key != LEASE_DURATION_US
        or bytes(row["renewal_payload"]) != _renewal_payload(record)
    ):
        raise IntegrityFailure("stored Renewal payload, sequence, or Lease disagrees")
    return record


class DispatchOutboxClaimLeaseStore:
    """One private pinned AIO-054 experiment ledger."""

    def __init__(
        self,
        configuration: StoreConfiguration,
        *,
        clock: object,
        fault_hook: FaultHook | None = None,
        allow_fenced: bool = False,
    ) -> None:
        self._initialize(
            configuration,
            clock=clock,
            fault_hook=fault_hook,
            expected_version=CURRENT_SCHEMA_VERSION,
            allow_fenced=allow_fenced,
        )

    @classmethod
    def open(
        cls,
        configuration: StoreConfiguration,
        *,
        clock: object,
        fault_hook: FaultHook | None = None,
        allow_fenced: bool = False,
    ) -> "DispatchOutboxClaimLeaseStore":
        return cls(
            configuration,
            clock=clock,
            fault_hook=fault_hook,
            allow_fenced=allow_fenced,
        )

    @classmethod
    def open_legacy(
        cls,
        configuration: StoreConfiguration,
        *,
        clock: object,
        fault_hook: FaultHook | None = None,
        allow_fenced: bool = False,
    ) -> "DispatchOutboxClaimLeaseStore":
        store = cls.__new__(cls)
        store._initialize(
            configuration,
            clock=clock,
            fault_hook=fault_hook,
            expected_version=LEGACY_SCHEMA_VERSION,
            allow_fenced=allow_fenced,
        )
        return store

    def _initialize(
        self,
        configuration: StoreConfiguration,
        *,
        clock: object,
        fault_hook: FaultHook | None,
        expected_version: int,
        allow_fenced: bool,
    ) -> None:
        self.configuration = _validate_configuration(configuration, require_file=True)
        if not callable(clock) and not callable(getattr(clock, "now_utc", None)):
            raise ConfigurationError("clock must be callable or implement now_utc()")
        if fault_hook is not None and not callable(fault_hook):
            raise ConfigurationError("fault_hook must be callable")
        if type(allow_fenced) is not bool:
            raise ConfigurationError("allow_fenced must be an exact boolean")
        self._clock = clock
        self._fault_hook = fault_hook
        self._expected_version = expected_version
        connection = self._open_verified(allow_fenced=allow_fenced)
        connection.close()

    @classmethod
    def provision_legacy(
        cls,
        configuration: StoreConfiguration,
        *,
        revocation_state_complete: bool = True,
        fault_hook: FaultHook | None = None,
    ) -> OperationResult:
        try:
            config = _validate_configuration(configuration, require_file=False)
            if type(revocation_state_complete) is not bool:
                raise ConfigurationError(
                    "revocation_state_complete must be an exact boolean"
                )
            if fault_hook is not None and not callable(fault_hook):
                raise ConfigurationError("fault_hook must be callable")
            old_fingerprint = _reference_fingerprint(LEGACY_SCHEMA_VERSION)
            old_manifest = _manifest_id(LEGACY_SCHEMA_VERSION)
            migration = _migration_entries(LEGACY_SCHEMA_VERSION)[0]
        except (ConfigurationError, IncompatibleSchemaError, ValueError) as error:
            return _result("storage_unavailable", str(error), retry="remediate")

        path = config.database_path
        if path.exists():
            return _result(
                "storage_unavailable",
                "provisioning refuses an existing path",
                retry="do_not_retry",
            )
        connection: sqlite3.Connection | None = None
        created = False
        commit_possible = False
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            created = True
            connection = sqlite3.connect(
                path.as_uri() + "?mode=rw",
                uri=True,
                timeout=BUSY_TIMEOUT_MS / 1_000,
                isolation_level=None,
            )
            profile = _configure_connection(connection, config, establish_wal=True)
            _fault(fault_hook, "provision.before_transaction")
            connection.execute("BEGIN IMMEDIATE")
            _fault(fault_hook, "provision.after_begin")
            _apply_statements(connection, _LEGACY_SCHEMA_SQL)
            connection.execute(
                "INSERT INTO experiment_schema_migrations VALUES (?, ?, ?)", migration
            )
            connection.execute(
                """
                INSERT INTO experiment_metadata (
                    singleton, store_id, application_id, authorization_domain_id,
                    schema_version, schema_manifest_id, schema_fingerprint,
                    ledger_instance_id, domain_generation, activation_state,
                    migration_state, revocation_state_complete,
                    last_decision_time, last_decision_time_key
                ) VALUES (1, ?, ?, ?, 1, ?, ?, ?, ?, 'active', 'clean', ?, NULL, NULL)
                """,
                (
                    STORE_ID,
                    APPLICATION_ID,
                    _text_bytes(config.authorization_domain_id, "authorization_domain_id"),
                    old_manifest,
                    old_fingerprint,
                    _text_bytes(config.ledger_instance_id, "ledger_instance_id"),
                    config.domain_generation,
                    int(revocation_state_complete),
                ),
            )
            connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
            connection.execute(f"PRAGMA user_version={LEGACY_SCHEMA_VERSION}")
            _fault(fault_hook, "provision.after_schema")
            commit_possible = True
            _fault(fault_hook, "provision.before_commit")
            connection.execute("COMMIT")
            _fault(fault_hook, "provision.after_commit")
            return _result("provisioned", committed=True, profile=profile)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown", str(error), retry="reconcile_administrative", committed=None
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown",
                    str(error),
                    retry="reconcile_administrative",
                    committed=None,
                )
            outcome = "storage_busy" if _is_busy(error) else "provision_failure"
            return _result(outcome, str(error), retry="remediate", committed=False)
        finally:
            if connection is not None:
                connection.close()
            if created and not commit_possible:
                for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass

    @classmethod
    def migrate_legacy(
        cls,
        configuration: StoreConfiguration,
        *,
        fault_hook: FaultHook | None = None,
    ) -> OperationResult:
        try:
            config = _validate_configuration(configuration, require_file=True)
            if fault_hook is not None and not callable(fault_hook):
                raise ConfigurationError("fault_hook must be callable")
            new_sql = _schema_bytes().decode("utf-8")
            new_fingerprint = _reference_fingerprint(CURRENT_SCHEMA_VERSION)
            new_manifest = _manifest_id(CURRENT_SCHEMA_VERSION)
            migration = _migration_entries(CURRENT_SCHEMA_VERSION)[1]
        except (ConfigurationError, IncompatibleSchemaError, ValueError) as error:
            return _result("migration_failure", str(error), retry="remediate")

        connection: sqlite3.Connection | None = None
        commit_possible = False
        try:
            connection = open_profiled_connection(config)
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version == CURRENT_SCHEMA_VERSION:
                connection.execute("BEGIN")
                cls._verify_connection_static(
                    connection, config, CURRENT_SCHEMA_VERSION, allow_fenced=False
                )
                connection.execute("ROLLBACK")
                return _result("already_migrated")
            if version != LEGACY_SCHEMA_VERSION:
                return _result(
                    "incompatible_schema",
                    "only the exact private version-1 ledger can migrate",
                    retry="remediate",
                )
            _fault(fault_hook, "migration.before_transaction")
            connection.execute("BEGIN EXCLUSIVE")
            _fault(fault_hook, "migration.after_begin")
            cls._verify_connection_static(
                connection, config, LEGACY_SCHEMA_VERSION, allow_fenced=False
            )
            connection.execute(
                "UPDATE experiment_metadata SET migration_state='dirty' WHERE singleton=1"
            )
            _fault(fault_hook, "migration.after_dirty")
            _apply_statements(connection, new_sql)
            _fault(fault_hook, "migration.after_schema")
            admissions = connection.execute(
                "SELECT * FROM experiment_admissions ORDER BY decision_time_key"
            ).fetchall()
            for row in admissions:
                identity = _identity_from_row(row)
                connection.execute(
                    """
                    INSERT INTO legacy_admission_markers (
                        authorization_domain_id, issuer_kind, issuer_id, grant_id,
                        migration_id, marker_payload
                    ) VALUES (?, ?, ?, ?, 2, ?)
                    """,
                    (*_identity_bytes(identity), _marker_payload(identity)),
                )
            _fault(fault_hook, "migration.after_legacy_population")
            cls._verify_xor(connection)
            connection.execute(
                "INSERT INTO experiment_schema_migrations VALUES (?, ?, ?)", migration
            )
            connection.execute(f"PRAGMA user_version={CURRENT_SCHEMA_VERSION}")
            connection.execute(
                """
                UPDATE experiment_metadata
                SET schema_version=?, schema_manifest_id=?, schema_fingerprint=?,
                    migration_state='clean'
                WHERE singleton=1 AND migration_state='dirty'
                """,
                (CURRENT_SCHEMA_VERSION, new_manifest, new_fingerprint),
            )
            _fault(fault_hook, "migration.after_clean_transition")
            cls._verify_connection_static(
                connection, config, CURRENT_SCHEMA_VERSION, allow_fenced=False
            )
            commit_possible = True
            _fault(fault_hook, "migration.before_commit")
            connection.execute("COMMIT")
            _fault(fault_hook, "migration.after_commit")
            return _result("migrated", committed=True)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown", str(error), retry="reconcile_administrative", committed=None
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown",
                    str(error),
                    retry="reconcile_administrative",
                    committed=None,
                )
            if _is_busy(error):
                return _result("storage_busy", str(error), retry="retry_exact", committed=False)
            if isinstance(error, IncompatibleSchemaError):
                outcome = "incompatible_schema"
            elif isinstance(error, IntegrityFailure):
                outcome = "integrity_failure"
            elif isinstance(error, InjectedFault):
                outcome = "fault_injected"
            else:
                outcome = "migration_failure"
            return _result(outcome, str(error), retry="remediate", committed=False)
        finally:
            if connection is not None:
                connection.close()

    def _open_verified(self, *, allow_fenced: bool) -> sqlite3.Connection:
        connection: sqlite3.Connection | None = None
        try:
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN")
            self._verify_connection_static(
                connection,
                self.configuration,
                self._expected_version,
                allow_fenced=allow_fenced,
            )
            connection.execute("ROLLBACK")
            return connection
        except BaseException:
            _safe_rollback(connection)
            if connection is not None:
                connection.close()
            raise

    @staticmethod
    def _verify_connection_static(
        connection: sqlite3.Connection,
        configuration: StoreConfiguration,
        expected_version: int,
        *,
        allow_fenced: bool,
    ) -> _Metadata:
        try:
            application_id = int(
                connection.execute("PRAGMA application_id").fetchone()[0]
            )
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if application_id != APPLICATION_ID:
                raise IncompatibleSchemaError(
                    "SQLite application_id does not identify the private experiment"
                )
            if user_version != expected_version:
                direction = "newer" if user_version > expected_version else "older"
                raise IncompatibleSchemaError(
                    f"experiment schema is {direction} than required version {expected_version}"
                )
            expected_fingerprint = _reference_fingerprint(expected_version)
            if _schema_fingerprint(connection) != expected_fingerprint:
                raise IntegrityFailure("sqlite_schema fingerprint mismatch")
            integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
            if len(integrity_rows) != 1 or integrity_rows[0][0] != "ok":
                raise IntegrityFailure("SQLite integrity_check failed")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise IntegrityFailure("SQLite foreign_key_check failed")
            DispatchOutboxClaimLeaseStore._verify_migration_history(
                connection, expected_version
            )
            metadata = DispatchOutboxClaimLeaseStore._verify_metadata(
                connection,
                configuration,
                expected_version,
                allow_fenced=allow_fenced,
            )
            highest_key = DispatchOutboxClaimLeaseStore._verify_base_records(connection)
            if expected_version == CURRENT_SCHEMA_VERSION:
                highest_key = max(
                    highest_key,
                    DispatchOutboxClaimLeaseStore._verify_new_records(connection),
                )
            if highest_key != MIN_SIGNED_64 and (
                metadata.watermark_key is None
                or metadata.watermark_key < highest_key
            ):
                raise IntegrityFailure("watermark trails durable decision history")
            return metadata
        except (IntegrityFailure, IncompatibleSchemaError):
            raise
        except (sqlite3.Error, KeyError, IndexError, TypeError, ValueError) as error:
            raise IntegrityFailure("experiment ledger verification failed closed") from error

    @staticmethod
    def _verify_migration_history(
        connection: sqlite3.Connection,
        expected_version: int,
    ) -> None:
        rows = connection.execute(
            """
            SELECT migration_id, resource_name, sha256
            FROM experiment_schema_migrations
            ORDER BY migration_id
            """
        ).fetchall()
        actual = tuple(
            (row["migration_id"], row["resource_name"], row["sha256"]) for row in rows
        )
        if actual != _migration_entries(expected_version):
            raise IntegrityFailure(
                "migration history is missing, noncontiguous, or checksum-mismatched"
            )

    @staticmethod
    def _verify_metadata(
        connection: sqlite3.Connection,
        configuration: StoreConfiguration,
        expected_version: int,
        *,
        allow_fenced: bool,
    ) -> _Metadata:
        rows = connection.execute("SELECT * FROM experiment_metadata").fetchall()
        if len(rows) != 1:
            raise IntegrityFailure("experiment metadata is not singleton")
        row = rows[0]
        if (
            row["singleton"] != 1
            or row["store_id"] != STORE_ID
            or row["application_id"] != APPLICATION_ID
            or row["authorization_domain_id"]
            != _text_bytes(configuration.authorization_domain_id, "authorization_domain_id")
            or row["schema_version"] != expected_version
            or row["schema_manifest_id"] != _manifest_id(expected_version)
            or row["schema_fingerprint"] != _reference_fingerprint(expected_version)
            or row["ledger_instance_id"]
            != _text_bytes(configuration.ledger_instance_id, "ledger_instance_id")
            or row["domain_generation"] != configuration.domain_generation
            or row["migration_state"] != "clean"
            or row["revocation_state_complete"] not in (0, 1)
        ):
            raise IntegrityFailure("experiment metadata is malformed or mismatched")
        activation = row["activation_state"]
        if activation not in ("active", "fenced"):
            raise IntegrityFailure("activation state is invalid")
        if activation == "fenced" and not allow_fenced:
            raise IncompatibleSchemaError("experiment ledger is terminally fenced")
        watermark_text = row["last_decision_time"]
        watermark_key = row["last_decision_time_key"]
        if watermark_text is None and watermark_key is None:
            pass
        elif type(watermark_text) is str and type(watermark_key) is int:
            _parse_time(watermark_text, watermark_key)
        else:
            raise IntegrityFailure("watermark text/key pair is incoherent")
        return _Metadata(
            activation_state=activation,
            revocation_state_complete=bool(row["revocation_state_complete"]),
            watermark_text=watermark_text,
            watermark_key=watermark_key,
        )

    @staticmethod
    def _verify_base_records(connection: sqlite3.Connection) -> int:
        highest_key = MIN_SIGNED_64
        admissions: dict[tuple[bytes, bytes, bytes, bytes], AdmissionRecord] = {}
        for row in connection.execute("SELECT * FROM experiment_admissions").fetchall():
            record = _admission_from_row(row)
            key = _identity_bytes(record.identity)
            if key in admissions:
                raise IntegrityFailure("duplicate logical Admission identity")
            if not (
                record.issued_at_key
                <= record.decision_time_key
                < record.expires_at_key
            ):
                raise IntegrityFailure("durable Admission decision is outside authority interval")
            admissions[key] = record
            highest_key = max(highest_key, record.decision_time_key)
        for row in connection.execute("SELECT * FROM experiment_revocations").fetchall():
            identity = _identity_from_row(row)
            identity_key = _identity_bytes(identity)
            run_id = _decode_text(row["run_id"], "run_id")
            grant_payload = bytes(row["grant_payload"])
            if not grant_payload:
                raise IntegrityFailure("stored revocation Grant payload is empty")
            _parse_time(row["revoked_at"], row["revoked_at_key"])
            expected_payload = _revocation_payload(
                identity,
                run_id,
                grant_payload,
                row["revoked_at"],
                row["revoked_at_key"],
            )
            if bytes(row["revocation_payload"]) != expected_payload:
                raise IntegrityFailure("stored revocation payload/index values disagree")
            admission = admissions.get(identity_key)
            if admission is not None and (
                admission.run_id != run_id
                or admission.grant_payload != grant_payload
                or row["revoked_at_key"] < admission.decision_time_key
            ):
                raise IntegrityFailure("revocation rebounds or predates Admission history")
            highest_key = max(highest_key, row["revoked_at_key"])
        return highest_key

    @staticmethod
    def _verify_xor(connection: sqlite3.Connection) -> None:
        admission_keys = {
            (
                row["authorization_domain_id"],
                row["issuer_kind"],
                row["issuer_id"],
                row["grant_id"],
            )
            for row in connection.execute(
                """
                SELECT authorization_domain_id, issuer_kind, issuer_id, grant_id
                FROM experiment_admissions
                """
            ).fetchall()
        }
        intent_keys = {
            (
                row["authorization_domain_id"],
                row["issuer_kind"],
                row["issuer_id"],
                row["grant_id"],
            )
            for row in connection.execute(
                """
                SELECT authorization_domain_id, issuer_kind, issuer_id, grant_id
                FROM dispatch_intents
                """
            ).fetchall()
        }
        marker_keys = {
            (
                row["authorization_domain_id"],
                row["issuer_kind"],
                row["issuer_id"],
                row["grant_id"],
            )
            for row in connection.execute(
                """
                SELECT authorization_domain_id, issuer_kind, issuer_id, grant_id
                FROM legacy_admission_markers
                """
            ).fetchall()
        }
        if (
            intent_keys & marker_keys
            or intent_keys | marker_keys != admission_keys
            or not intent_keys <= admission_keys
            or not marker_keys <= admission_keys
        ):
            raise IntegrityFailure(
                "every Admission must have exactly one Intent or legacy marker"
            )

    @staticmethod
    def _verify_new_records(connection: sqlite3.Connection) -> int:
        DispatchOutboxClaimLeaseStore._verify_xor(connection)
        highest_key = MIN_SIGNED_64
        admissions = {
            _identity_bytes(record.identity): record
            for record in (
                _admission_from_row(row)
                for row in connection.execute("SELECT * FROM experiment_admissions")
            )
        }
        for row in connection.execute("SELECT * FROM legacy_admission_markers"):
            identity = _identity_from_row(row)
            if row["migration_id"] != CURRENT_SCHEMA_VERSION:
                raise IntegrityFailure("legacy marker migration identity is invalid")
            if bytes(row["marker_payload"]) != _marker_payload(identity):
                raise IntegrityFailure("legacy marker payload/index values disagree")
        intents: dict[tuple[bytes, bytes, bytes, bytes], IntentRecord] = {}
        for row in connection.execute("SELECT * FROM dispatch_intents"):
            intent = _intent_from_row(row)
            key = _identity_bytes(intent.identity)
            admission = admissions.get(key)
            if admission is None or (
                intent.run_id != admission.run_id
                or intent.admission_decision_time != admission.decision_time
                or intent.admission_decision_time_key != admission.decision_time_key
            ):
                raise IntegrityFailure("Intent does not exactly bind its Admission")
            intents[key] = intent

        claims_by_identity: dict[
            tuple[bytes, bytes, bytes, bytes], list[ClaimRecord]
        ] = {}
        claims_by_id: dict[str, ClaimRecord] = {}
        for row in connection.execute("SELECT * FROM dispatch_claims"):
            claim = _claim_from_row(row)
            key = _identity_bytes(claim.identity)
            if key not in intents:
                raise IntegrityFailure("Claim does not bind a Dispatch Intent")
            if claim.claim_id in claims_by_id:
                raise IntegrityFailure("duplicate Claim ID")
            claims_by_id[claim.claim_id] = claim
            claims_by_identity.setdefault(key, []).append(claim)
            highest_key = max(highest_key, claim.acquired_at_key)
        for claims in claims_by_identity.values():
            ordered = sorted(claims, key=lambda item: item.lease_generation)
            expected = list(range(1, len(ordered) + 1))
            if [item.lease_generation for item in ordered] != expected:
                raise IntegrityFailure("Claim generations are gapped or rebound")

        renewals_by_claim: dict[str, list[RenewalRecord]] = {}
        seen_renewal_ids: set[str] = set()
        for row in connection.execute("SELECT * FROM lease_renewals"):
            renewal = _renewal_from_row(row)
            if renewal.renewal_id in seen_renewal_ids:
                raise IntegrityFailure("duplicate Renewal ID")
            seen_renewal_ids.add(renewal.renewal_id)
            claim = claims_by_id.get(renewal.claim_id)
            if claim is None or (
                renewal.identity != claim.identity
                or renewal.executor_instance_id != claim.executor_instance_id
                or renewal.lease_generation != claim.lease_generation
            ):
                raise IntegrityFailure("Renewal rebounds from its exact Claim")
            renewals_by_claim.setdefault(renewal.claim_id, []).append(renewal)
            highest_key = max(highest_key, renewal.renewed_at_key)
        for claim_id, renewals in renewals_by_claim.items():
            claim = claims_by_id[claim_id]
            ordered = sorted(renewals, key=lambda item: item.renewal_sequence)
            expected = list(range(1, len(ordered) + 1))
            if [item.renewal_sequence for item in ordered] != expected:
                raise IntegrityFailure("Renewal sequence is gapped, duplicate, or nonpositive")
            effective = claim.lease_until_key
            for renewal in ordered:
                if renewal.lease_until_key <= effective:
                    raise IntegrityFailure("Renewal chain does not strictly extend expiry")
                effective = renewal.lease_until_key
        return highest_key

    def _metadata(self, connection: sqlite3.Connection) -> _Metadata:
        return self._verify_connection_static(
            connection,
            self.configuration,
            self._expected_version,
            allow_fenced=False,
        )

    def _sample_clock(self, metadata: _Metadata) -> tuple[datetime, str, int]:
        try:
            source = self._clock
            sampled = source() if callable(source) else source.now_utc()
            instant, text, key = _canonical_time(sampled)
        except BaseException as error:
            raise ClockFailure(f"trusted UTC clock failed closed: {error}") from error
        if metadata.watermark_key is not None and key < metadata.watermark_key:
            raise ClockRegression("trusted UTC clock precedes the durable watermark")
        return instant, text, key

    @staticmethod
    def _advance_watermark(
        connection: sqlite3.Connection,
        text: str,
        key: int,
    ) -> None:
        cursor = connection.execute(
            """
            UPDATE experiment_metadata
            SET last_decision_time=?, last_decision_time_key=?
            WHERE singleton=1 AND activation_state='active'
              AND migration_state='clean'
              AND (last_decision_time_key IS NULL OR last_decision_time_key <= ?)
            """,
            (text, key, key),
        )
        if cursor.rowcount != 1:
            raise IntegrityFailure("watermark update lost active-ledger ownership")

    def _operation_failure(self, error: BaseException) -> OperationResult:
        if isinstance(error, ClockRegression):
            return _result("clock_regression", str(error), retry="remediate")
        if isinstance(error, ClockFailure):
            return _result("clock_failure", str(error), retry="remediate")
        if isinstance(error, IncompatibleSchemaError):
            return _result("incompatible_schema", str(error), retry="remediate")
        if isinstance(error, IntegrityFailure):
            return _result("integrity_failure", str(error), retry="remediate")
        if isinstance(error, InjectedFault):
            return _result("fault_injected", str(error), retry="retry_exact", committed=False)
        if _is_busy(error):
            return _result("storage_busy", str(error), retry="retry_exact")
        return _result("storage_unavailable", str(error), retry="remediate")

    def connection_profile(self) -> ConnectionProfile:
        connection = self._open_verified(allow_fenced=False)
        try:
            return _connection_profile(connection)
        finally:
            connection.close()

    def watermark(self) -> tuple[str | None, int | None]:
        connection = self._open_verified(allow_fenced=False)
        try:
            metadata = self._verify_metadata(
                connection,
                self.configuration,
                self._expected_version,
                allow_fenced=False,
            )
            return metadata.watermark_text, metadata.watermark_key
        finally:
            connection.close()

    def _validate_admission_request(
        self,
        request: object,
    ) -> tuple[
        AdmissionRequest,
        tuple[bytes, bytes, bytes, bytes],
        bytes,
        tuple[datetime, str, int],
        tuple[datetime, str, int],
    ]:
        if type(request) is not AdmissionRequest:
            raise ValueError("request must be the exact AdmissionRequest type")
        identity_bytes = _identity_bytes(request.identity)
        if request.authorization_domain_id != self.configuration.authorization_domain_id:
            raise ValueError("Admission request domain does not match the pinned ledger")
        run_id = _text_bytes(request.run_id, "run_id")
        _require_payload(request.grant_payload, "grant_payload")
        _require_payload(request.binding_payload, "binding_payload")
        issued = _canonical_time(request.issued_at)
        expires = _canonical_time(request.expires_at)
        if issued[2] >= expires[2]:
            raise ValueError("Grant authority interval must be nonempty")
        return request, identity_bytes, run_id, issued, expires

    @staticmethod
    def _find_admission(
        connection: sqlite3.Connection,
        identity_bytes: tuple[bytes, bytes, bytes, bytes],
    ) -> AdmissionRecord | None:
        row = connection.execute(
            """
            SELECT * FROM experiment_admissions
            WHERE authorization_domain_id=? AND issuer_kind=?
              AND issuer_id=? AND grant_id=?
            """,
            identity_bytes,
        ).fetchone()
        return None if row is None else _admission_from_row(row)

    @staticmethod
    def _find_admission_by_run(
        connection: sqlite3.Connection,
        domain: bytes,
        run_id: bytes,
    ) -> AdmissionRecord | None:
        row = connection.execute(
            """
            SELECT * FROM experiment_admissions
            WHERE authorization_domain_id=? AND run_id=?
            """,
            (domain, run_id),
        ).fetchone()
        return None if row is None else _admission_from_row(row)

    @staticmethod
    def _find_intent(
        connection: sqlite3.Connection,
        identity_bytes: tuple[bytes, bytes, bytes, bytes],
    ) -> IntentRecord | None:
        row = connection.execute(
            """
            SELECT * FROM dispatch_intents
            WHERE authorization_domain_id=? AND issuer_kind=?
              AND issuer_id=? AND grant_id=?
            """,
            identity_bytes,
        ).fetchone()
        return None if row is None else _intent_from_row(row)

    @staticmethod
    def _has_legacy_marker(
        connection: sqlite3.Connection,
        identity_bytes: tuple[bytes, bytes, bytes, bytes],
    ) -> bool:
        return connection.execute(
            """
            SELECT 1 FROM legacy_admission_markers
            WHERE authorization_domain_id=? AND issuer_kind=?
              AND issuer_id=? AND grant_id=?
            """,
            identity_bytes,
        ).fetchone() is not None

    def _classify_admission_history(
        self,
        connection: sqlite3.Connection,
        request: AdmissionRequest,
        identity_bytes: tuple[bytes, bytes, bytes, bytes],
        run_id: bytes,
        issued: tuple[datetime, str, int],
        expires: tuple[datetime, str, int],
    ) -> OperationResult | None:
        existing = self._find_admission(connection, identity_bytes)
        if existing is not None:
            same_grant = (
                existing.run_id == request.run_id
                and existing.grant_payload == request.grant_payload
                and existing.issued_at == issued[1]
                and existing.issued_at_key == issued[2]
                and existing.expires_at == expires[1]
                and existing.expires_at_key == expires[2]
            )
            if not same_grant:
                return _result(
                    "grant_identity_conflict",
                    "Grant composite identity is bound to different complete values",
                    retry="do_not_retry",
                )
            if existing.binding_payload != request.binding_payload:
                return _result(
                    "binding_conflict",
                    "complete Grant is bound to another Binding",
                    retry="do_not_retry",
                )
            if self._expected_version == LEGACY_SCHEMA_VERSION:
                return _result(
                    "existing_legacy_admission",
                    "exact pre-dispatch Admission history",
                    admission=existing,
                    exact_history=True,
                    committed=True,
                )
            intent = self._find_intent(connection, identity_bytes)
            marker = self._has_legacy_marker(connection, identity_bytes)
            if marker and intent is None:
                return _result(
                    "existing_legacy_admission",
                    "exact legacy Admission remains non-dispatchable",
                    admission=existing,
                    exact_history=True,
                    committed=True,
                )
            if intent is None or marker:
                raise IntegrityFailure("exact Admission has incoherent XOR classification")
            return _result(
                "existing_exact_admission",
                "exact Admission and Intent history",
                admission=existing,
                intent=intent,
                exact_history=True,
                committed=True,
            )
        run_existing = self._find_admission_by_run(
            connection, identity_bytes[0], run_id
        )
        if run_existing is not None:
            return _result(
                "run_conflict",
                "authorization domain and Run ID are already admitted",
                retry="do_not_retry",
            )
        return None

    def admit_legacy(
        self,
        request: AdmissionRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        if self._expected_version != LEGACY_SCHEMA_VERSION:
            return _result("incompatible_schema", "admit_legacy requires a version-1 store")
        return self._admit(request, with_intent=False, post_check=post_check)

    def admit(
        self,
        request: AdmissionRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        if self._expected_version != CURRENT_SCHEMA_VERSION:
            return _result("incompatible_schema", "admit requires a migrated store")
        return self._admit(request, with_intent=True, post_check=post_check)

    def _admit(
        self,
        request: AdmissionRequest,
        *,
        with_intent: bool,
        post_check: PostCheck | None,
    ) -> OperationResult:
        try:
            request, identity_bytes, run_id, issued, expires = (
                self._validate_admission_request(request)
            )
        except (TypeError, ValueError) as error:
            return _result("invalid_input", str(error), retry="do_not_retry")

        prefix = "admission" if with_intent else "legacy_admission"
        connection: sqlite3.Connection | None = None
        commit_possible = False
        admission: AdmissionRecord | None = None
        intent: IntentRecord | None = None
        try:
            _fault(self._fault_hook, f"{prefix}.before_transaction")
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            _fault(self._fault_hook, f"{prefix}.after_begin")
            metadata = self._metadata(connection)
            history = self._classify_admission_history(
                connection, request, identity_bytes, run_id, issued, expires
            )
            if history is not None:
                connection.execute("ROLLBACK")
                if not _post_check(post_check):
                    return _result(
                        "lifecycle_lost",
                        "post-Store lifecycle revalidation failed",
                        retry="retry_exact",
                    )
                return history
            if not metadata.revocation_state_complete:
                connection.execute("ROLLBACK")
                return _result(
                    "revocation_incomplete",
                    "revocation evidence is incomplete",
                    retry="remediate",
                )
            revocation = connection.execute(
                """
                SELECT * FROM experiment_revocations
                WHERE authorization_domain_id=? AND issuer_kind=?
                  AND issuer_id=? AND grant_id=?
                """,
                identity_bytes,
            ).fetchone()
            sampled, decision_text, decision_key = self._sample_clock(metadata)
            if decision_key < issued[2]:
                self._advance_watermark(connection, decision_text, decision_key)
                commit_possible = True
                _fault(self._fault_hook, f"{prefix}.before_commit")
                connection.execute("COMMIT")
                _fault(self._fault_hook, f"{prefix}.after_commit")
                return _result("not_yet_current", committed=True, retry="retry_later")
            if decision_key >= expires[2]:
                self._advance_watermark(connection, decision_text, decision_key)
                commit_possible = True
                _fault(self._fault_hook, f"{prefix}.before_commit")
                connection.execute("COMMIT")
                _fault(self._fault_hook, f"{prefix}.after_commit")
                return _result("expired", committed=True, retry="do_not_retry")
            if revocation is not None:
                stored_run = _decode_text(revocation["run_id"], "run_id")
                if (
                    stored_run != request.run_id
                    or bytes(revocation["grant_payload"]) != request.grant_payload
                ):
                    connection.execute("ROLLBACK")
                    return _result(
                        "grant_identity_conflict",
                        "revocation identity is bound to another complete Grant",
                        retry="do_not_retry",
                    )
                self._advance_watermark(connection, decision_text, decision_key)
                commit_possible = True
                _fault(self._fault_hook, f"{prefix}.before_commit")
                connection.execute("COMMIT")
                _fault(self._fault_hook, f"{prefix}.after_commit")
                return _result("revoked", committed=True, retry="do_not_retry")

            admission = AdmissionRecord(
                identity=request.identity,
                run_id=request.run_id,
                grant_payload=request.grant_payload,
                binding_payload=request.binding_payload,
                issued_at=issued[1],
                issued_at_key=issued[2],
                expires_at=expires[1],
                expires_at_key=expires[2],
                decision_time=decision_text,
                decision_time_key=decision_key,
            )
            connection.execute(
                """
                INSERT INTO experiment_admissions (
                    authorization_domain_id, issuer_kind, issuer_id, grant_id,
                    run_id, grant_payload, binding_payload,
                    issued_at, issued_at_key, expires_at, expires_at_key,
                    decision_time, decision_time_key, admission_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *identity_bytes,
                    run_id,
                    request.grant_payload,
                    request.binding_payload,
                    issued[1],
                    issued[2],
                    expires[1],
                    expires[2],
                    decision_text,
                    decision_key,
                    _admission_payload(
                        request,
                        issued[1],
                        issued[2],
                        expires[1],
                        expires[2],
                        decision_text,
                        decision_key,
                    ),
                ),
            )
            _fault(self._fault_hook, f"{prefix}.after_admission_insert")
            if with_intent:
                intent = IntentRecord(
                    identity=request.identity,
                    run_id=request.run_id,
                    admission_decision_time=decision_text,
                    admission_decision_time_key=decision_key,
                )
                connection.execute(
                    """
                    INSERT INTO dispatch_intents (
                        authorization_domain_id, issuer_kind, issuer_id, grant_id,
                        run_id, admission_decision_time,
                        admission_decision_time_key, intent_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        *identity_bytes,
                        run_id,
                        decision_text,
                        decision_key,
                        _intent_payload(intent),
                    ),
                )
                _fault(self._fault_hook, "admission.after_intent_insert")
                self._verify_xor(connection)
            self._advance_watermark(connection, decision_text, decision_key)
            _fault(self._fault_hook, f"{prefix}.after_watermark")
            commit_possible = True
            _fault(self._fault_hook, f"{prefix}.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, f"{prefix}.after_commit")
            if not _post_check(post_check):
                return _result(
                    "lifecycle_lost",
                    "post-Store lifecycle revalidation failed after possible commit",
                    retry="retry_exact",
                    committed=True,
                )
            return _result(
                "newly_admitted" if with_intent else "newly_legacy_admitted",
                admission=admission,
                intent=intent,
                committed=True,
            )
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown", str(error), retry="retry_exact", committed=None
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown", str(error), retry="retry_exact", committed=None
                )
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def revoke(
        self,
        request: AdmissionRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        try:
            request, identity_bytes, run_id, _, _ = self._validate_admission_request(
                request
            )
        except (TypeError, ValueError) as error:
            return _result("invalid_input", str(error), retry="do_not_retry")
        connection: sqlite3.Connection | None = None
        commit_possible = False
        try:
            _fault(self._fault_hook, "revocation.before_transaction")
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            _fault(self._fault_hook, "revocation.after_begin")
            metadata = self._metadata(connection)
            existing = connection.execute(
                """
                SELECT * FROM experiment_revocations
                WHERE authorization_domain_id=? AND issuer_kind=?
                  AND issuer_id=? AND grant_id=?
                """,
                identity_bytes,
            ).fetchone()
            if existing is not None:
                if (
                    _decode_text(existing["run_id"], "run_id") != request.run_id
                    or bytes(existing["grant_payload"]) != request.grant_payload
                ):
                    connection.execute("ROLLBACK")
                    return _result("grant_identity_conflict", retry="do_not_retry")
                connection.execute("ROLLBACK")
                return _result("existing_exact_revocation", exact_history=True)
            admitted = self._find_admission(connection, identity_bytes)
            if admitted is not None and (
                admitted.run_id != request.run_id
                or admitted.grant_payload != request.grant_payload
            ):
                connection.execute("ROLLBACK")
                return _result("grant_identity_conflict", retry="do_not_retry")
            _, revoked_text, revoked_key = self._sample_clock(metadata)
            payload = _revocation_payload(
                request.identity,
                request.run_id,
                request.grant_payload,
                revoked_text,
                revoked_key,
            )
            connection.execute(
                """
                INSERT INTO experiment_revocations (
                    authorization_domain_id, issuer_kind, issuer_id, grant_id,
                    run_id, grant_payload, revoked_at, revoked_at_key,
                    revocation_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *identity_bytes,
                    run_id,
                    request.grant_payload,
                    revoked_text,
                    revoked_key,
                    payload,
                ),
            )
            _fault(self._fault_hook, "revocation.after_insert")
            self._advance_watermark(connection, revoked_text, revoked_key)
            commit_possible = True
            _fault(self._fault_hook, "revocation.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, "revocation.after_commit")
            if not _post_check(post_check):
                return _result(
                    "lifecycle_lost", retry="retry_exact", committed=True
                )
            return _result("newly_revoked", committed=True)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result("commit_unknown", str(error), retry="retry_exact")
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result("commit_unknown", str(error), retry="retry_exact")
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def set_revocation_completeness(self) -> OperationResult:
        """Irreversibly transition experiment revocation evidence from 0 to 1."""

        connection: sqlite3.Connection | None = None
        try:
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            self._metadata(connection)
            connection.execute(
                """
                UPDATE experiment_metadata
                SET revocation_state_complete=1
                WHERE singleton=1 AND revocation_state_complete=0
                """
            )
            connection.execute("COMMIT")
            return _result("revocation_evidence_complete", committed=True)
        except Exception as error:
            _safe_rollback(connection)
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _find_claim_by_id(
        connection: sqlite3.Connection,
        claim_id: bytes,
    ) -> ClaimRecord | None:
        row = connection.execute(
            "SELECT * FROM dispatch_claims WHERE claim_id=?", (claim_id,)
        ).fetchone()
        return None if row is None else _claim_from_row(row)

    @staticmethod
    def _highest_claim(
        connection: sqlite3.Connection,
        identity: DispatchIdentity,
    ) -> ClaimRecord | None:
        row = connection.execute(
            """
            SELECT * FROM dispatch_claims
            WHERE authorization_domain_id=? AND issuer_kind=?
              AND issuer_id=? AND grant_id=?
            ORDER BY lease_generation DESC
            LIMIT 1
            """,
            _identity_bytes(identity),
        ).fetchone()
        return None if row is None else _claim_from_row(row)

    @staticmethod
    def _effective_expiry(
        connection: sqlite3.Connection,
        claim: ClaimRecord,
    ) -> tuple[str, int]:
        rows = connection.execute(
            """
            SELECT * FROM lease_renewals
            WHERE claim_id=?
            ORDER BY renewal_sequence
            """,
            (_text_bytes(claim.claim_id, "claim_id"),),
        ).fetchall()
        effective_text = claim.lease_until
        effective_key = claim.lease_until_key
        expected_sequence = 1
        for row in rows:
            renewal = _renewal_from_row(row)
            if (
                renewal.identity != claim.identity
                or renewal.executor_instance_id != claim.executor_instance_id
                or renewal.lease_generation != claim.lease_generation
                or renewal.renewal_sequence != expected_sequence
                or renewal.lease_until_key <= effective_key
            ):
                raise IntegrityFailure("effective Renewal chain is invalid")
            effective_text = renewal.lease_until
            effective_key = renewal.lease_until_key
            expected_sequence += 1
        return effective_text, effective_key

    @staticmethod
    def _is_revoked(
        connection: sqlite3.Connection,
        identity: DispatchIdentity,
    ) -> bool:
        return connection.execute(
            """
            SELECT 1 FROM experiment_revocations
            WHERE authorization_domain_id=? AND issuer_kind=?
              AND issuer_id=? AND grant_id=?
            """,
            _identity_bytes(identity),
        ).fetchone() is not None

    def claim(
        self,
        request: ClaimRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        if self._expected_version != CURRENT_SCHEMA_VERSION:
            return _result("incompatible_schema", "claim requires a migrated store")
        try:
            if type(request) is not ClaimRequest:
                raise ValueError("request must be the exact ClaimRequest type")
            claim_id = _text_bytes(request.claim_id, "claim_id")
            executor_id = _text_bytes(
                request.executor_instance_id, "executor_instance_id"
            )
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")

        connection: sqlite3.Connection | None = None
        commit_possible = False
        inserted = False
        try:
            _fault(self._fault_hook, "claim.before_transaction")
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            _fault(self._fault_hook, "claim.after_begin")
            metadata = self._metadata(connection)
            _fault(self._fault_hook, "claim.after_invariant_validation")
            history = self._find_claim_by_id(connection, claim_id)
            if history is not None:
                if history.executor_instance_id != request.executor_instance_id:
                    connection.execute("ROLLBACK")
                    return _result(
                        "executor_conflict",
                        "committed Claim ID is bound to another Executor",
                        retry="do_not_retry",
                    )
                connection.execute("ROLLBACK")
                if not _post_check(post_check):
                    return _result("lifecycle_lost", retry="retry_exact")
                return _result(
                    "existing_claim_history",
                    "immutable history only; current authority requires assessment",
                    claim=history,
                    exact_history=True,
                    committed=True,
                )

            intent_rows = connection.execute(
                """
                SELECT i.*
                FROM dispatch_intents AS i
                JOIN experiment_admissions AS a
                  ON a.authorization_domain_id=i.authorization_domain_id
                 AND a.issuer_kind=i.issuer_kind
                 AND a.issuer_id=i.issuer_id
                 AND a.grant_id=i.grant_id
                ORDER BY a.decision_time_key ASC,
                         i.authorization_domain_id ASC,
                         i.issuer_kind ASC,
                         i.issuer_id ASC,
                         i.grant_id ASC
                """
            ).fetchall()
            if not intent_rows:
                connection.execute("ROLLBACK")
                return _result("empty", reevaluation=True, committed=False)
            if not metadata.revocation_state_complete:
                connection.execute("ROLLBACK")
                return _result(
                    "authority_ineligible",
                    "revocation evidence is incomplete",
                    reevaluation=True,
                    committed=False,
                )
            eligible: list[IntentRecord] = []
            for row in intent_rows:
                intent = _intent_from_row(row)
                if not self._is_revoked(connection, intent.identity):
                    eligible.append(intent)
            if not eligible:
                connection.execute("ROLLBACK")
                return _result(
                    "authority_ineligible",
                    "no Intent has complete current revocation eligibility",
                    reevaluation=True,
                    committed=False,
                )

            _, now_text, now_key = self._sample_clock(metadata)
            _fault(self._fault_hook, "claim.after_clock_sample")
            selected: IntentRecord | None = None
            prior: ClaimRecord | None = None
            for intent in eligible:
                highest = self._highest_claim(connection, intent.identity)
                if highest is None:
                    selected = intent
                    prior = None
                    break
                _, effective_key = self._effective_expiry(connection, highest)
                if now_key >= effective_key:
                    selected = intent
                    prior = highest
                    break
            if selected is None:
                self._advance_watermark(connection, now_text, now_key)
                _fault(self._fault_hook, "claim.after_watermark")
                commit_possible = True
                _fault(self._fault_hook, "claim.before_commit")
                connection.execute("COMMIT")
                _fault(self._fault_hook, "claim.after_commit")
                return _result(
                    "temporarily_unavailable",
                    "all authority-eligible Intents have active Leases",
                    reevaluation=True,
                    committed=True,
                )
            generation = 1 if prior is None else prior.lease_generation + 1
            if generation <= 0 or generation > MAX_SIGNED_64:
                raise IntegrityFailure("Lease generation is exhausted")
            lease_key = now_key + LEASE_DURATION_US
            if lease_key > MAX_SIGNED_64:
                raise IntegrityFailure("Claim Lease timestamp overflows signed 64-bit time")
            try:
                _, lease_text, checked_lease_key = _time_from_key(lease_key)
            except ValueError as error:
                raise ClockFailure("Claim Lease expiry is out of range") from error
            claim = ClaimRecord(
                claim_id=request.claim_id,
                identity=selected.identity,
                executor_instance_id=request.executor_instance_id,
                lease_generation=generation,
                acquired_at=now_text,
                acquired_at_key=now_key,
                lease_until=lease_text,
                lease_until_key=checked_lease_key,
            )
            connection.execute(
                """
                INSERT INTO dispatch_claims (
                    claim_id, authorization_domain_id, issuer_kind, issuer_id,
                    grant_id, executor_instance_id, lease_generation,
                    acquired_at, acquired_at_key, lease_until, lease_until_key,
                    claim_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    *_identity_bytes(selected.identity),
                    executor_id,
                    generation,
                    now_text,
                    now_key,
                    lease_text,
                    checked_lease_key,
                    _claim_payload(claim),
                ),
            )
            inserted = True
            _fault(self._fault_hook, "claim.after_insert")
            self._advance_watermark(connection, now_text, now_key)
            _fault(self._fault_hook, "claim.after_watermark")
            commit_possible = True
            _fault(self._fault_hook, "claim.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, "claim.after_commit")
            if not _post_check(post_check):
                return _result(
                    "lifecycle_lost",
                    "post-Store lifecycle revalidation failed after possible Claim commit",
                    retry="retry_exact",
                    committed=True,
                )
            return _result("newly_claimed", claim=claim, committed=True)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown",
                str(error),
                retry="retry_exact" if inserted else "reevaluate",
                reevaluation=not inserted,
                committed=None,
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown",
                    str(error),
                    retry="retry_exact" if inserted else "reevaluate",
                    reevaluation=not inserted,
                    committed=None,
                )
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def renew(
        self,
        request: RenewalRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        if self._expected_version != CURRENT_SCHEMA_VERSION:
            return _result("incompatible_schema", "renew requires a migrated store")
        try:
            if type(request) is not RenewalRequest:
                raise ValueError("request must be the exact RenewalRequest type")
            identity_bytes = _identity_bytes(request.identity)
            if request.identity.authorization_domain_id != self.configuration.authorization_domain_id:
                raise ValueError("Renewal domain does not match the pinned ledger")
            claim_id = _text_bytes(request.claim_id, "claim_id")
            executor_id = _text_bytes(
                request.executor_instance_id, "executor_instance_id"
            )
            renewal_id = _text_bytes(request.renewal_id, "renewal_id")
            if (
                type(request.lease_generation) is not int
                or request.lease_generation <= 0
                or request.lease_generation > MAX_SIGNED_64
            ):
                raise ValueError("lease_generation must be a positive signed-64 integer")
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")

        connection: sqlite3.Connection | None = None
        commit_possible = False
        inserted = False
        try:
            _fault(self._fault_hook, "renewal.before_transaction")
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            _fault(self._fault_hook, "renewal.after_begin")
            metadata = self._metadata(connection)
            _fault(self._fault_hook, "renewal.after_invariant_validation")
            historical_row = connection.execute(
                "SELECT * FROM lease_renewals WHERE renewal_id=?", (renewal_id,)
            ).fetchone()
            if historical_row is not None:
                historical = _renewal_from_row(historical_row)
                if (
                    historical.claim_id != request.claim_id
                    or historical.identity != request.identity
                    or historical.executor_instance_id != request.executor_instance_id
                    or historical.lease_generation != request.lease_generation
                ):
                    connection.execute("ROLLBACK")
                    return _result("renewal_identity_conflict", retry="do_not_retry")
                connection.execute("ROLLBACK")
                if not _post_check(post_check):
                    return _result("lifecycle_lost", retry="retry_exact")
                return _result(
                    "existing_renewal_history",
                    "immutable history only; current authority requires assessment",
                    renewal=historical,
                    exact_history=True,
                    committed=True,
                )

            claim = self._find_claim_by_id(connection, claim_id)
            if claim is None:
                connection.execute("ROLLBACK")
                return _result("claim_not_found", retry="do_not_retry")
            if (
                claim.identity != request.identity
                or claim.executor_instance_id != request.executor_instance_id
                or claim.lease_generation != request.lease_generation
            ):
                connection.execute("ROLLBACK")
                return _result("claim_identity_conflict", retry="do_not_retry")
            highest = self._highest_claim(connection, request.identity)
            if highest is None or highest.claim_id != request.claim_id:
                connection.execute("ROLLBACK")
                return _result("stale_generation", retry="do_not_retry")
            if not metadata.revocation_state_complete:
                connection.execute("ROLLBACK")
                return _result("revocation_incomplete", retry="remediate")
            if self._is_revoked(connection, request.identity):
                connection.execute("ROLLBACK")
                return _result("revoked", retry="do_not_retry")

            _, now_text, now_key = self._sample_clock(metadata)
            _fault(self._fault_hook, "renewal.after_clock_sample")
            effective_text, effective_key = self._effective_expiry(connection, claim)
            candidate_key = now_key + LEASE_DURATION_US
            if candidate_key > MAX_SIGNED_64:
                raise IntegrityFailure("Renewal Lease timestamp overflows signed 64-bit time")
            if now_key >= effective_key or candidate_key <= effective_key:
                self._advance_watermark(connection, now_text, now_key)
                _fault(self._fault_hook, "renewal.after_watermark")
                commit_possible = True
                _fault(self._fault_hook, "renewal.before_commit")
                connection.execute("COMMIT")
                _fault(self._fault_hook, "renewal.after_commit")
                outcome = "expired_claim" if now_key >= effective_key else "nonextending"
                return _result(
                    outcome,
                    reevaluation=True,
                    committed=True,
                    retry="reevaluate",
                )
            sequence_row = connection.execute(
                "SELECT MAX(renewal_sequence) FROM lease_renewals WHERE claim_id=?",
                (claim_id,),
            ).fetchone()
            previous_sequence = sequence_row[0]
            sequence = 1 if previous_sequence is None else previous_sequence + 1
            if sequence <= 0 or sequence > MAX_SIGNED_64:
                raise IntegrityFailure("Renewal sequence is exhausted")
            try:
                _, lease_text, checked_lease_key = _time_from_key(candidate_key)
            except ValueError as error:
                raise ClockFailure("Renewal Lease expiry is out of range") from error
            renewal = RenewalRecord(
                renewal_id=request.renewal_id,
                claim_id=request.claim_id,
                identity=request.identity,
                executor_instance_id=request.executor_instance_id,
                lease_generation=request.lease_generation,
                renewal_sequence=sequence,
                renewed_at=now_text,
                renewed_at_key=now_key,
                lease_until=lease_text,
                lease_until_key=checked_lease_key,
            )
            connection.execute(
                """
                INSERT INTO lease_renewals (
                    renewal_id, claim_id, authorization_domain_id, issuer_kind,
                    issuer_id, grant_id, executor_instance_id, lease_generation,
                    renewal_sequence, renewed_at, renewed_at_key,
                    lease_until, lease_until_key, renewal_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    renewal_id,
                    claim_id,
                    *identity_bytes,
                    executor_id,
                    request.lease_generation,
                    sequence,
                    now_text,
                    now_key,
                    lease_text,
                    checked_lease_key,
                    _renewal_payload(renewal),
                ),
            )
            inserted = True
            _fault(self._fault_hook, "renewal.after_insert")
            self._advance_watermark(connection, now_text, now_key)
            _fault(self._fault_hook, "renewal.after_watermark")
            commit_possible = True
            _fault(self._fault_hook, "renewal.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, "renewal.after_commit")
            if not _post_check(post_check):
                return _result(
                    "lifecycle_lost",
                    retry="retry_exact",
                    committed=True,
                )
            return _result("renewed", renewal=renewal, committed=True)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown",
                str(error),
                retry="retry_exact" if inserted else "reevaluate",
                reevaluation=not inserted,
                committed=None,
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown",
                    str(error),
                    retry="retry_exact" if inserted else "reevaluate",
                    reevaluation=not inserted,
                    committed=None,
                )
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def assess_current_claim(
        self,
        request: CurrentClaimRequest,
        *,
        post_check: PostCheck | None = None,
    ) -> OperationResult:
        if self._expected_version != CURRENT_SCHEMA_VERSION:
            return _result("incompatible_schema", "assessment requires a migrated store")
        try:
            if type(request) is not CurrentClaimRequest:
                raise ValueError("request must be the exact CurrentClaimRequest type")
            _identity_bytes(request.identity)
            if request.identity.authorization_domain_id != self.configuration.authorization_domain_id:
                raise ValueError("assessment domain does not match the pinned ledger")
            claim_id = _text_bytes(request.claim_id, "claim_id")
            _text_bytes(request.executor_instance_id, "executor_instance_id")
            if (
                type(request.lease_generation) is not int
                or request.lease_generation <= 0
                or request.lease_generation > MAX_SIGNED_64
            ):
                raise ValueError("lease_generation must be a positive signed-64 integer")
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")

        connection: sqlite3.Connection | None = None
        commit_possible = False
        try:
            _fault(self._fault_hook, "assessment.before_transaction")
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            _fault(self._fault_hook, "assessment.after_begin")
            metadata = self._metadata(connection)
            claim = self._find_claim_by_id(connection, claim_id)
            if claim is None:
                connection.execute("ROLLBACK")
                return _result("claim_not_found", retry="do_not_retry")
            if (
                claim.identity != request.identity
                or claim.executor_instance_id != request.executor_instance_id
                or claim.lease_generation != request.lease_generation
            ):
                connection.execute("ROLLBACK")
                return _result("claim_identity_conflict", retry="do_not_retry")
            effective_text, effective_key = self._effective_expiry(connection, claim)
            highest = self._highest_claim(connection, request.identity)
            if highest is None or highest.claim_id != request.claim_id:
                connection.execute("ROLLBACK")
                assessment = CurrentClaimAssessment(
                    status="inactive",
                    reason="superseded_generation",
                    claim=claim,
                    effective_lease_until=effective_text,
                    effective_lease_until_key=effective_key,
                    observed_at=None,
                    observed_at_key=None,
                )
                return _result("inactive", assessment=assessment, committed=False)
            if not metadata.revocation_state_complete:
                connection.execute("ROLLBACK")
                return _result("revocation_incomplete", retry="remediate")
            if self._is_revoked(connection, request.identity):
                connection.execute("ROLLBACK")
                return _result("revoked", retry="do_not_retry")
            _, now_text, now_key = self._sample_clock(metadata)
            _fault(self._fault_hook, "assessment.after_clock_sample")
            active = claim.acquired_at_key <= now_key < effective_key
            assessment = CurrentClaimAssessment(
                status="active" if active else "inactive",
                reason="unexpired" if active else "expired",
                claim=claim,
                effective_lease_until=effective_text,
                effective_lease_until_key=effective_key,
                observed_at=now_text,
                observed_at_key=now_key,
            )
            self._advance_watermark(connection, now_text, now_key)
            _fault(self._fault_hook, "assessment.after_watermark")
            commit_possible = True
            _fault(self._fault_hook, "assessment.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, "assessment.after_commit")
            if not _post_check(post_check):
                return _result(
                    "lifecycle_lost",
                    "post-Store lifecycle revalidation returned no current authority",
                    committed=True,
                )
            return _result(
                assessment.status,
                assessment=assessment,
                committed=True,
            )
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown", str(error), retry="reevaluate", committed=None
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown", str(error), retry="reevaluate", committed=None
                )
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def _open_administrative_read(self) -> sqlite3.Connection:
        connection = open_profiled_connection(self.configuration)
        try:
            connection.execute("BEGIN")
            self._verify_connection_static(
                connection,
                self.configuration,
                self._expected_version,
                allow_fenced=True,
            )
            return connection
        except BaseException:
            _safe_rollback(connection)
            connection.close()
            raise

    def audit_admission(self, identity: DispatchIdentity) -> OperationResult:
        """Read immutable same-ledger history without returning authority."""

        try:
            identity_bytes = _identity_bytes(identity)
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")
        connection: sqlite3.Connection | None = None
        try:
            connection = self._open_administrative_read()
            admission = self._find_admission(connection, identity_bytes)
            intent = (
                self._find_intent(connection, identity_bytes)
                if self._expected_version == CURRENT_SCHEMA_VERSION
                else None
            )
            connection.execute("ROLLBACK")
            if admission is None:
                return _result("not_found")
            return _result(
                "audited_admission_history",
                "non-authoritative administrative history",
                admission=admission,
                intent=intent,
                exact_history=True,
                committed=True,
            )
        except Exception as error:
            _safe_rollback(connection)
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def audit_claim(self, claim_id: str) -> OperationResult:
        try:
            encoded = _text_bytes(claim_id, "claim_id")
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")
        connection: sqlite3.Connection | None = None
        try:
            connection = self._open_administrative_read()
            claim = self._find_claim_by_id(connection, encoded)
            connection.execute("ROLLBACK")
            if claim is None:
                return _result("not_found")
            return _result(
                "audited_claim_history",
                "non-authoritative administrative history",
                claim=claim,
                exact_history=True,
                committed=True,
            )
        except Exception as error:
            _safe_rollback(connection)
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def audit_renewal(self, renewal_id: str) -> OperationResult:
        try:
            encoded = _text_bytes(renewal_id, "renewal_id")
        except ValueError as error:
            return _result("invalid_input", str(error), retry="do_not_retry")
        connection: sqlite3.Connection | None = None
        try:
            connection = self._open_administrative_read()
            row = connection.execute(
                "SELECT * FROM lease_renewals WHERE renewal_id=?", (encoded,)
            ).fetchone()
            connection.execute("ROLLBACK")
            if row is None:
                return _result("not_found")
            return _result(
                "audited_renewal_history",
                "non-authoritative administrative history",
                renewal=_renewal_from_row(row),
                exact_history=True,
                committed=True,
            )
        except Exception as error:
            _safe_rollback(connection)
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def fence(self) -> OperationResult:
        connection: sqlite3.Connection | None = None
        commit_possible = False
        try:
            connection = open_profiled_connection(self.configuration)
            connection.execute("BEGIN IMMEDIATE")
            metadata = self._verify_connection_static(
                connection,
                self.configuration,
                self._expected_version,
                allow_fenced=True,
            )
            if metadata.activation_state == "fenced":
                connection.execute("ROLLBACK")
                return _result("already_fenced", committed=True)
            _fault(self._fault_hook, "fence.before_update")
            cursor = connection.execute(
                """
                UPDATE experiment_metadata
                SET activation_state='fenced'
                WHERE singleton=1 AND activation_state='active'
                """
            )
            if cursor.rowcount != 1:
                raise IntegrityFailure("terminal fence lost active ownership")
            _fault(self._fault_hook, "fence.after_update")
            commit_possible = True
            _fault(self._fault_hook, "fence.before_commit")
            connection.execute("COMMIT")
            _fault(self._fault_hook, "fence.after_commit")
            return _result("fenced", committed=True)
        except CommitUnknownFault as error:
            _safe_rollback(connection)
            return _result(
                "commit_unknown", str(error), retry="reconcile_administrative"
            )
        except Exception as error:
            _safe_rollback(connection)
            if commit_possible:
                return _result(
                    "commit_unknown", str(error), retry="reconcile_administrative"
                )
            return self._operation_failure(error)
        finally:
            if connection is not None:
                connection.close()
