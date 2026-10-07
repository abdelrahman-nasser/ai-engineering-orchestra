-- AIO-054 private experiment schema extension (version 2).
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
