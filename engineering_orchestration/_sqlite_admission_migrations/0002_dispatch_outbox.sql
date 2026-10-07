-- AIO-055 additive durable Dispatch Intent foundation, schema version 2.
-- Existing v1 Admissions are classified only as non-dispatchable legacy history.
-- The administrative transaction appends migration 2 before deferred FK commit.

CREATE TABLE agent_execution_dispatch_intents (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (authorization_domain_id <> ''),
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind IN ('human', 'policy')),
    issuer_id TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL
        CHECK (grant_id <> ''),
    PRIMARY KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id),
    FOREIGN KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        REFERENCES agent_execution_dispatch_admissions
            (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE TABLE legacy_admission_markers (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (authorization_domain_id <> ''),
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind IN ('human', 'policy')),
    issuer_id TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL
        CHECK (grant_id <> ''),
    migration_id INTEGER NOT NULL CHECK (migration_id = 2),
    PRIMARY KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id),
    FOREIGN KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        REFERENCES agent_execution_dispatch_admissions
            (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (migration_id)
        REFERENCES admission_schema_migrations (migration_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED
) STRICT, WITHOUT ROWID;

CREATE TRIGGER agent_execution_dispatch_intents_operational_insert
BEFORE INSERT ON agent_execution_dispatch_intents
WHEN NOT EXISTS (
    SELECT 1 FROM admission_ledger_metadata
    WHERE singleton = 1 AND activation_state = 'active'
      AND migration_state = 'clean' AND schema_version = 2
)
BEGIN
    SELECT RAISE(ABORT, 'Intent insertion requires active clean v2 state');
END;

CREATE TRIGGER legacy_admission_markers_migration_insert
BEFORE INSERT ON legacy_admission_markers
WHEN NOT EXISTS (
    SELECT 1 FROM admission_ledger_metadata
    WHERE singleton = 1 AND activation_state = 'active'
      AND migration_state = 'dirty' AND schema_version = 1
)
BEGIN
    SELECT RAISE(ABORT, 'Legacy insertion requires the dirty v1 migration');
END;

CREATE TRIGGER agent_execution_dispatch_intents_no_duplicate
BEFORE INSERT ON agent_execution_dispatch_intents
WHEN EXISTS (
    SELECT 1 FROM agent_execution_dispatch_intents
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intent identity cannot be replaced');
END;

CREATE TRIGGER legacy_admission_markers_no_duplicate
BEFORE INSERT ON legacy_admission_markers
WHEN EXISTS (
    SELECT 1 FROM legacy_admission_markers
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Legacy marker identity cannot be replaced');
END;

CREATE TRIGGER agent_execution_dispatch_intents_no_legacy_overlap
BEFORE INSERT ON agent_execution_dispatch_intents
WHEN EXISTS (
    SELECT 1 FROM legacy_admission_markers
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intent overlaps legacy history');
END;

CREATE TRIGGER legacy_admission_markers_no_intent_overlap
BEFORE INSERT ON legacy_admission_markers
WHEN EXISTS (
    SELECT 1 FROM agent_execution_dispatch_intents
    WHERE authorization_domain_id = NEW.authorization_domain_id
      AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
      AND grant_id = NEW.grant_id
)
BEGIN
    SELECT RAISE(ABORT, 'Legacy marker overlaps a Dispatch Intent');
END;

CREATE TRIGGER agent_execution_dispatch_intents_no_update
BEFORE UPDATE ON agent_execution_dispatch_intents
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intents are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_intents_no_delete
BEFORE DELETE ON agent_execution_dispatch_intents
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Intents are immutable');
END;

CREATE TRIGGER legacy_admission_markers_no_update
BEFORE UPDATE ON legacy_admission_markers
BEGIN
    SELECT RAISE(ABORT, 'Legacy markers are immutable');
END;

CREATE TRIGGER legacy_admission_markers_no_delete
BEFORE DELETE ON legacy_admission_markers
BEGIN
    SELECT RAISE(ABORT, 'Legacy markers are immutable');
END;

INSERT INTO legacy_admission_markers (
    authorization_domain_id, issuer_kind, issuer_id, grant_id, migration_id
)
SELECT authorization_domain_id, issuer_kind, issuer_id, grant_id, 2
FROM agent_execution_dispatch_admissions;
