-- AIO-047 production SQLite Admission ledger, schema version 1.
-- Provisioning supplies the singleton metadata and migration-history rows.

CREATE TABLE admission_ledger_metadata (
    singleton INTEGER NOT NULL PRIMARY KEY
        CHECK (singleton = 1),
    store_id TEXT COLLATE BINARY NOT NULL
        CHECK (store_id <> ''),
    application_id INTEGER NOT NULL,
    authorization_domain_id TEXT COLLATE BINARY NOT NULL UNIQUE
        CHECK (authorization_domain_id <> ''),
    schema_version INTEGER NOT NULL
        CHECK (schema_version >= 1),
    schema_manifest_id TEXT COLLATE BINARY NOT NULL
        CHECK (schema_manifest_id <> ''),
    ledger_instance_id TEXT COLLATE BINARY NOT NULL
        CHECK (ledger_instance_id <> ''),
    domain_generation INTEGER NOT NULL
        CHECK (domain_generation > 0),
    activation_state TEXT COLLATE BINARY NOT NULL
        CHECK (activation_state IN ('active', 'fenced')),
    migration_state TEXT COLLATE BINARY NOT NULL
        CHECK (migration_state IN ('clean', 'dirty')),
    revocation_state_complete INTEGER NOT NULL
        CHECK (revocation_state_complete = 1),
    last_decision_time TEXT COLLATE BINARY,
    last_decision_time_key INTEGER,
    CHECK (
        (last_decision_time IS NULL AND last_decision_time_key IS NULL)
        OR
        (
            last_decision_time IS NOT NULL
            AND last_decision_time <> ''
            AND last_decision_time_key IS NOT NULL
        )
    )
) STRICT;

CREATE TABLE admission_schema_migrations (
    migration_id INTEGER NOT NULL PRIMARY KEY,
    resource_name TEXT COLLATE BINARY NOT NULL UNIQUE
        CHECK (resource_name <> ''),
    sha256 TEXT COLLATE BINARY NOT NULL
        CHECK (length(sha256) = 64)
) STRICT;

CREATE TABLE agent_execution_dispatch_admissions (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL,
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind <> ''),
    issuer_id TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL
        CHECK (grant_id <> ''),
    run_id TEXT COLLATE BINARY NOT NULL
        CHECK (run_id <> ''),
    grant_json TEXT COLLATE BINARY NOT NULL
        CHECK (grant_json <> ''),
    binding_json TEXT COLLATE BINARY NOT NULL
        CHECK (binding_json <> ''),
    admission_json TEXT COLLATE BINARY NOT NULL
        CHECK (admission_json <> ''),
    decision_time TEXT COLLATE BINARY NOT NULL
        CHECK (decision_time <> ''),
    decision_time_key INTEGER NOT NULL,
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES admission_ledger_metadata (authorization_domain_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE UNIQUE INDEX admission_domain_run_unique
ON agent_execution_dispatch_admissions (
    authorization_domain_id,
    run_id
);

CREATE TABLE agent_execution_grant_revocations (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL,
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind <> ''),
    issuer_id TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL
        CHECK (grant_id <> ''),
    run_id TEXT COLLATE BINARY NOT NULL
        CHECK (run_id <> ''),
    grant_json TEXT COLLATE BINARY NOT NULL
        CHECK (grant_json <> ''),
    revoker_kind TEXT COLLATE BINARY NOT NULL,
    revoker_id TEXT COLLATE BINARY NOT NULL,
    revocation_time TEXT COLLATE BINARY NOT NULL
        CHECK (revocation_time <> ''),
    revocation_time_key INTEGER NOT NULL,
    PRIMARY KEY (
        authorization_domain_id,
        issuer_kind,
        issuer_id,
        grant_id
    ),
    FOREIGN KEY (authorization_domain_id)
        REFERENCES admission_ledger_metadata (authorization_domain_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CHECK (revoker_kind = issuer_kind AND revoker_id = issuer_id)
) STRICT, WITHOUT ROWID;

CREATE TRIGGER admission_ledger_metadata_insert_once
BEFORE INSERT ON admission_ledger_metadata
WHEN EXISTS (SELECT 1 FROM admission_ledger_metadata)
BEGIN
    SELECT RAISE(ABORT, 'Admission ledger metadata already exists');
END;

CREATE TRIGGER admission_ledger_metadata_no_delete
BEFORE DELETE ON admission_ledger_metadata
BEGIN
    SELECT RAISE(ABORT, 'Admission ledger metadata cannot be deleted');
END;

CREATE TRIGGER admission_ledger_metadata_transition_guard
BEFORE UPDATE ON admission_ledger_metadata
WHEN
    NEW.singleton IS NOT OLD.singleton
    OR NEW.store_id IS NOT OLD.store_id
    OR NEW.application_id IS NOT OLD.application_id
    OR NEW.authorization_domain_id IS NOT OLD.authorization_domain_id
    OR NEW.ledger_instance_id IS NOT OLD.ledger_instance_id
    OR NEW.domain_generation IS NOT OLD.domain_generation
    OR NEW.revocation_state_complete IS NOT OLD.revocation_state_complete
    OR (
        OLD.activation_state = 'fenced'
        AND NEW.activation_state <> 'fenced'
    )
    OR NOT (
        (OLD.migration_state = 'clean' AND NEW.migration_state IN ('clean', 'dirty'))
        OR
        (OLD.migration_state = 'dirty' AND NEW.migration_state IN ('dirty', 'clean'))
    )
    OR NEW.schema_version < OLD.schema_version
    OR (
        (
            NEW.schema_version IS NOT OLD.schema_version
            OR NEW.schema_manifest_id IS NOT OLD.schema_manifest_id
        )
        AND OLD.migration_state <> 'dirty'
    )
BEGIN
    SELECT RAISE(ABORT, 'Admission ledger metadata transition is prohibited');
END;

CREATE TRIGGER admission_ledger_watermark_monotonic
BEFORE UPDATE ON admission_ledger_metadata
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
    SELECT RAISE(ABORT, 'Admission ledger watermark cannot regress or rebound');
END;

CREATE TRIGGER admission_schema_migrations_contiguous
BEFORE INSERT ON admission_schema_migrations
WHEN NEW.migration_id <> COALESCE(
    (SELECT MAX(migration_id) + 1 FROM admission_schema_migrations),
    1
)
BEGIN
    SELECT RAISE(ABORT, 'Admission migration history must be contiguous');
END;

CREATE TRIGGER admission_schema_migrations_no_update
BEFORE UPDATE ON admission_schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'Admission migration history is immutable');
END;

CREATE TRIGGER admission_schema_migrations_no_delete
BEFORE DELETE ON admission_schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'Admission migration history is immutable');
END;

CREATE TRIGGER agent_execution_dispatch_admissions_no_revoked_insert
BEFORE INSERT ON agent_execution_dispatch_admissions
WHEN EXISTS (
    SELECT 1
    FROM agent_execution_grant_revocations
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'A revoked Grant cannot be admitted');
END;

CREATE TRIGGER agent_execution_dispatch_admissions_no_update
BEFORE UPDATE ON agent_execution_dispatch_admissions
BEGIN
    SELECT RAISE(ABORT, 'Admissions are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_admissions_no_delete
BEFORE DELETE ON agent_execution_dispatch_admissions
BEGIN
    SELECT RAISE(ABORT, 'Admissions are immutable');
END;

CREATE TRIGGER agent_execution_grant_revocations_no_rebound
BEFORE INSERT ON agent_execution_grant_revocations
WHEN EXISTS (
    SELECT 1
    FROM agent_execution_dispatch_admissions
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind
      AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
      AND grant_json <> NEW.grant_json
)
BEGIN
    SELECT RAISE(ABORT, 'Grant identity cannot rebound across security records');
END;

CREATE TRIGGER agent_execution_grant_revocations_no_update
BEFORE UPDATE ON agent_execution_grant_revocations
BEGIN
    SELECT RAISE(ABORT, 'Grant revocations are immutable');
END;

CREATE TRIGGER agent_execution_grant_revocations_no_delete
BEFORE DELETE ON agent_execution_grant_revocations
BEGIN
    SELECT RAISE(ABORT, 'Grant revocations are immutable');
END;
