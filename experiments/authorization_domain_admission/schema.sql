-- AIO-046 private experimental schema.
--
-- This DDL is not a canonical Core schema or a production store contract.
-- Provisioning inserts exactly one ledger_metadata row after installing it.

CREATE TABLE ledger_metadata (
    singleton INTEGER NOT NULL PRIMARY KEY
        CHECK (singleton = 1 AND typeof(singleton) = 'integer'),
    schema_version INTEGER NOT NULL
        CHECK (schema_version = 1 AND typeof(schema_version) = 'integer'),
    authorization_domain_id TEXT COLLATE BINARY NOT NULL UNIQUE
        CHECK (
            typeof(authorization_domain_id) = 'text'
            AND authorization_domain_id <> ''
        ),
    revocation_state_complete INTEGER NOT NULL CHECK (
        revocation_state_complete = 1
        AND typeof(revocation_state_complete) = 'integer'
    ),
    last_decision_time TEXT COLLATE BINARY,
    last_decision_time_key INTEGER,
    CHECK (
        (last_decision_time IS NULL AND last_decision_time_key IS NULL)
        OR
        (
            last_decision_time IS NOT NULL
            AND length(last_decision_time) > 0
            AND typeof(last_decision_time) = 'text'
            AND last_decision_time_key IS NOT NULL
            AND typeof(last_decision_time_key) = 'integer'
        )
    )
);

CREATE TABLE admissions (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (typeof(authorization_domain_id) = 'text'),
    issuer_kind TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(issuer_kind) = 'text' AND issuer_kind <> ''
    ),
    issuer_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(issuer_id) = 'text' AND issuer_id <> ''
    ),
    grant_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(grant_id) = 'text' AND grant_id <> ''
    ),
    run_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(run_id) = 'text' AND run_id <> ''
    ),
    grant_json TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(grant_json) = 'text' AND length(grant_json) > 0
    ),
    binding_json TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(binding_json) = 'text' AND length(binding_json) > 0
    ),
    decision_time TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(decision_time) = 'text' AND length(decision_time) > 0
    ),
    decision_time_key INTEGER NOT NULL
        CHECK (typeof(decision_time_key) = 'integer'),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    UNIQUE (authorization_domain_id, run_id),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES ledger_metadata (authorization_domain_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) WITHOUT ROWID;

CREATE TABLE revocations (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (typeof(authorization_domain_id) = 'text'),
    issuer_kind TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(issuer_kind) = 'text' AND issuer_kind <> ''
    ),
    issuer_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(issuer_id) = 'text' AND issuer_id <> ''
    ),
    grant_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(grant_id) = 'text' AND grant_id <> ''
    ),
    run_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(run_id) = 'text' AND run_id <> ''
    ),
    grant_json TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(grant_json) = 'text' AND length(grant_json) > 0
    ),
    revoker_kind TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(revoker_kind) = 'text' AND revoker_kind <> ''
    ),
    revoker_id TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(revoker_id) = 'text' AND revoker_id <> ''
    ),
    decision_time TEXT COLLATE BINARY NOT NULL CHECK (
        typeof(decision_time) = 'text' AND length(decision_time) > 0
    ),
    decision_time_key INTEGER NOT NULL
        CHECK (typeof(decision_time_key) = 'integer'),
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES ledger_metadata (authorization_domain_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CHECK (revoker_kind = issuer_kind AND revoker_id = issuer_id)
) WITHOUT ROWID;

CREATE TRIGGER ledger_metadata_insert_once
BEFORE INSERT ON ledger_metadata
WHEN EXISTS (SELECT 1 FROM ledger_metadata)
BEGIN
    SELECT RAISE(ABORT, 'ledger metadata singleton already exists');
END;

CREATE TRIGGER ledger_metadata_no_delete
BEFORE DELETE ON ledger_metadata
BEGIN
    SELECT RAISE(ABORT, 'ledger metadata is immutable');
END;

CREATE TRIGGER ledger_metadata_identity_immutable
BEFORE UPDATE ON ledger_metadata
WHEN
    NEW.singleton IS NOT OLD.singleton
    OR NEW.schema_version IS NOT OLD.schema_version
    OR NEW.authorization_domain_id IS NOT OLD.authorization_domain_id
    OR NEW.revocation_state_complete IS NOT OLD.revocation_state_complete
BEGIN
    SELECT RAISE(ABORT, 'ledger metadata identity and completeness are immutable');
END;

CREATE TRIGGER ledger_metadata_watermark_monotonic
BEFORE UPDATE ON ledger_metadata
WHEN
    (NEW.last_decision_time IS NULL) IS NOT
        (NEW.last_decision_time_key IS NULL)
    OR (
        OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key IS NULL
    )
    OR (
        OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key < OLD.last_decision_time_key
    )
    OR (
        OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key = OLD.last_decision_time_key
        AND NEW.last_decision_time IS NOT OLD.last_decision_time
    )
    OR (
        OLD.last_decision_time_key IS NOT NULL
        AND NEW.last_decision_time_key > OLD.last_decision_time_key
        AND NEW.last_decision_time IS OLD.last_decision_time
    )
BEGIN
    SELECT RAISE(ABORT, 'ledger decision-time watermark cannot regress or rebound');
END;

CREATE TRIGGER admissions_no_identity_reuse
BEFORE INSERT ON admissions
WHEN
    EXISTS (
        SELECT 1
        FROM admissions
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind
          AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    )
    OR EXISTS (
        SELECT 1
        FROM admissions
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND run_id = NEW.run_id
    )
BEGIN
    SELECT RAISE(ABORT, 'admission identity already exists');
END;

CREATE TRIGGER admissions_no_update
BEFORE UPDATE ON admissions
BEGIN
    SELECT RAISE(ABORT, 'admissions are immutable');
END;

CREATE TRIGGER admissions_no_delete
BEFORE DELETE ON admissions
BEGIN
    SELECT RAISE(ABORT, 'admissions are immutable');
END;

CREATE TRIGGER revocations_no_identity_reuse
BEFORE INSERT ON revocations
WHEN EXISTS (
    SELECT 1
    FROM revocations
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'revocation identity already exists');
END;

CREATE TRIGGER revocations_no_update
BEFORE UPDATE ON revocations
BEGIN
    SELECT RAISE(ABORT, 'revocations are immutable');
END;

CREATE TRIGGER revocations_no_delete
BEFORE DELETE ON revocations
BEGIN
    SELECT RAISE(ABORT, 'revocations are immutable');
END;
