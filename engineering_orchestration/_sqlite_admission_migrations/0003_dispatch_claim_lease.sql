-- AIO-056 private durable Dispatch Claim/Lease history, schema version 3.
-- Authority remains in the supported owned Store; no invocation is performed.

CREATE TABLE agent_execution_dispatch_claims (
    claim_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY
        CHECK (length(claim_id) = 64 AND claim_id NOT GLOB '*[^0-9a-f]*'),
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (authorization_domain_id <> ''),
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind IN ('human', 'policy')),
    issuer_id TEXT COLLATE BINARY NOT NULL CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL CHECK (grant_id <> ''),
    executor_instance_id TEXT COLLATE BINARY NOT NULL
        CHECK (length(executor_instance_id) = 64
               AND executor_instance_id NOT GLOB '*[^0-9a-f]*'),
    lease_generation INTEGER NOT NULL CHECK (lease_generation > 0),
    acquired_at TEXT COLLATE BINARY NOT NULL CHECK (length(acquired_at) = 27),
    acquired_at_key INTEGER NOT NULL
        CHECK (acquired_at_key BETWEEN 0 AND 315537897599999999),
    lease_until TEXT COLLATE BINARY NOT NULL CHECK (length(lease_until) = 27),
    lease_until_key INTEGER NOT NULL
        CHECK (lease_until_key BETWEEN 0 AND 315537897599999999),
    UNIQUE (authorization_domain_id, issuer_kind, issuer_id, grant_id,
            lease_generation),
    UNIQUE (claim_id, authorization_domain_id, issuer_kind, issuer_id,
            grant_id, executor_instance_id, lease_generation),
    FOREIGN KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        REFERENCES agent_execution_dispatch_intents
            (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (lease_until_key = acquired_at_key + 30000000
           AND lease_until_key > acquired_at_key)
) STRICT, WITHOUT ROWID;

CREATE TABLE agent_execution_dispatch_renewals (
    renewal_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY
        CHECK (length(renewal_id) = 64 AND renewal_id NOT GLOB '*[^0-9a-f]*'),
    claim_id TEXT COLLATE BINARY NOT NULL
        CHECK (length(claim_id) = 64 AND claim_id NOT GLOB '*[^0-9a-f]*'),
    authorization_domain_id TEXT COLLATE BINARY NOT NULL
        CHECK (authorization_domain_id <> ''),
    issuer_kind TEXT COLLATE BINARY NOT NULL
        CHECK (issuer_kind IN ('human', 'policy')),
    issuer_id TEXT COLLATE BINARY NOT NULL CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL CHECK (grant_id <> ''),
    executor_instance_id TEXT COLLATE BINARY NOT NULL
        CHECK (length(executor_instance_id) = 64
               AND executor_instance_id NOT GLOB '*[^0-9a-f]*'),
    lease_generation INTEGER NOT NULL CHECK (lease_generation > 0),
    renewal_sequence INTEGER NOT NULL CHECK (renewal_sequence > 0),
    renewed_at TEXT COLLATE BINARY NOT NULL CHECK (length(renewed_at) = 27),
    renewed_at_key INTEGER NOT NULL
        CHECK (renewed_at_key BETWEEN 0 AND 315537897599999999),
    lease_until TEXT COLLATE BINARY NOT NULL CHECK (length(lease_until) = 27),
    lease_until_key INTEGER NOT NULL
        CHECK (lease_until_key BETWEEN 0 AND 315537897599999999),
    UNIQUE (claim_id, renewal_sequence),
    FOREIGN KEY (claim_id, authorization_domain_id, issuer_kind, issuer_id,
                 grant_id, executor_instance_id, lease_generation)
        REFERENCES agent_execution_dispatch_claims
            (claim_id, authorization_domain_id, issuer_kind, issuer_id,
             grant_id, executor_instance_id, lease_generation)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (lease_until_key = renewed_at_key + 30000000
           AND lease_until_key > renewed_at_key)
) STRICT, WITHOUT ROWID;

DROP TRIGGER agent_execution_dispatch_intents_operational_insert;
CREATE TRIGGER agent_execution_dispatch_intents_operational_insert
BEFORE INSERT ON agent_execution_dispatch_intents
WHEN NOT EXISTS (
    SELECT 1 FROM admission_ledger_metadata
    WHERE singleton = 1 AND activation_state = 'active'
      AND migration_state = 'clean' AND schema_version = 3
)
BEGIN
    SELECT RAISE(ABORT, 'Intent insertion requires active clean v3 state');
END;

CREATE TRIGGER agent_execution_dispatch_claims_no_update
BEFORE UPDATE ON agent_execution_dispatch_claims
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Claims are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_claims_no_delete
BEFORE DELETE ON agent_execution_dispatch_claims
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Claims are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_claims_no_duplicate
BEFORE INSERT ON agent_execution_dispatch_claims
WHEN EXISTS (
    SELECT 1 FROM agent_execution_dispatch_claims
    WHERE claim_id = NEW.claim_id
       OR (authorization_domain_id = NEW.authorization_domain_id
           AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
           AND grant_id = NEW.grant_id AND lease_generation = NEW.lease_generation)
)
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Claim identity cannot be replaced');
END;

CREATE TRIGGER agent_execution_dispatch_claims_operational_insert
BEFORE INSERT ON agent_execution_dispatch_claims
WHEN NOT EXISTS (
    SELECT 1 FROM admission_ledger_metadata
    WHERE singleton = 1 AND activation_state = 'active'
      AND migration_state = 'clean' AND schema_version = 3
)
BEGIN
    SELECT RAISE(ABORT, 'Claim insertion requires active clean v3 state');
END;

CREATE TRIGGER agent_execution_dispatch_claims_history_insert_guard
BEFORE INSERT ON agent_execution_dispatch_claims
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM agent_execution_dispatch_intents
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ) OR EXISTS (
        SELECT 1 FROM legacy_admission_markers
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ) OR EXISTS (
        SELECT 1 FROM agent_execution_grant_revocations
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ) THEN RAISE(ABORT, 'Claim parent or revocation state is ineligible') END;
    SELECT CASE WHEN NEW.acquired_at_key < (
        SELECT decision_time_key FROM agent_execution_dispatch_admissions
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ) OR NEW.acquired_at_key < (
        SELECT last_decision_time_key FROM admission_ledger_metadata WHERE singleton = 1
    ) THEN RAISE(ABORT, 'Claim time regresses') END;
    SELECT CASE WHEN NEW.lease_generation <> COALESCE((
        SELECT MAX(lease_generation) + 1 FROM agent_execution_dispatch_claims
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ), 1) THEN RAISE(ABORT, 'Claim generation must be contiguous') END;
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM agent_execution_dispatch_claims AS c
        WHERE c.authorization_domain_id = NEW.authorization_domain_id
          AND c.issuer_kind = NEW.issuer_kind AND c.issuer_id = NEW.issuer_id
          AND c.grant_id = NEW.grant_id
          AND NEW.acquired_at_key < COALESCE((
              SELECT MAX(r.lease_until_key) FROM agent_execution_dispatch_renewals AS r
              WHERE r.claim_id = c.claim_id
          ), c.lease_until_key)
    ) THEN RAISE(ABORT, 'Claim overlaps prior effective Lease') END;
END;

CREATE TRIGGER agent_execution_dispatch_renewals_no_update
BEFORE UPDATE ON agent_execution_dispatch_renewals
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Renewals are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_renewals_no_delete
BEFORE DELETE ON agent_execution_dispatch_renewals
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Renewals are immutable');
END;

CREATE TRIGGER agent_execution_dispatch_renewals_no_duplicate
BEFORE INSERT ON agent_execution_dispatch_renewals
WHEN EXISTS (
    SELECT 1 FROM agent_execution_dispatch_renewals
    WHERE renewal_id = NEW.renewal_id
       OR (claim_id = NEW.claim_id AND renewal_sequence = NEW.renewal_sequence)
)
BEGIN
    SELECT RAISE(ABORT, 'Dispatch Renewal identity cannot be replaced');
END;

CREATE TRIGGER agent_execution_dispatch_renewals_operational_insert
BEFORE INSERT ON agent_execution_dispatch_renewals
WHEN NOT EXISTS (
    SELECT 1 FROM admission_ledger_metadata
    WHERE singleton = 1 AND activation_state = 'active'
      AND migration_state = 'clean' AND schema_version = 3
)
BEGIN
    SELECT RAISE(ABORT, 'Renewal insertion requires active clean v3 state');
END;

CREATE TRIGGER agent_execution_dispatch_renewals_history_insert_guard
BEFORE INSERT ON agent_execution_dispatch_renewals
BEGIN
    SELECT CASE WHEN NOT EXISTS (
        SELECT 1 FROM agent_execution_dispatch_claims AS c
        WHERE c.claim_id = NEW.claim_id
          AND c.authorization_domain_id = NEW.authorization_domain_id
          AND c.issuer_kind = NEW.issuer_kind AND c.issuer_id = NEW.issuer_id
          AND c.grant_id = NEW.grant_id
          AND c.executor_instance_id = NEW.executor_instance_id
          AND c.lease_generation = NEW.lease_generation
          AND c.lease_generation = (
              SELECT MAX(h.lease_generation) FROM agent_execution_dispatch_claims AS h
              WHERE h.authorization_domain_id = NEW.authorization_domain_id
                AND h.issuer_kind = NEW.issuer_kind AND h.issuer_id = NEW.issuer_id
                AND h.grant_id = NEW.grant_id
          )
    ) OR EXISTS (
        SELECT 1 FROM agent_execution_grant_revocations
        WHERE authorization_domain_id = NEW.authorization_domain_id
          AND issuer_kind = NEW.issuer_kind AND issuer_id = NEW.issuer_id
          AND grant_id = NEW.grant_id
    ) THEN RAISE(ABORT, 'Renewal requires exact current unrevoked Claim') END;
    SELECT CASE WHEN NEW.renewal_sequence <> COALESCE((
        SELECT MAX(renewal_sequence) + 1 FROM agent_execution_dispatch_renewals
        WHERE claim_id = NEW.claim_id
    ), 1) THEN RAISE(ABORT, 'Renewal sequence must be contiguous') END;
    SELECT CASE WHEN NEW.renewed_at_key < (
        SELECT acquired_at_key FROM agent_execution_dispatch_claims WHERE claim_id = NEW.claim_id
    ) OR NEW.renewed_at_key < (
        SELECT MAX(renewed_at_key) FROM agent_execution_dispatch_renewals WHERE claim_id = NEW.claim_id
    ) OR NEW.renewed_at_key < (
        SELECT last_decision_time_key FROM admission_ledger_metadata WHERE singleton = 1
    ) THEN RAISE(ABORT, 'Renewal time regresses') END;
    SELECT CASE WHEN NEW.renewed_at_key >= COALESCE((
        SELECT MAX(lease_until_key) FROM agent_execution_dispatch_renewals WHERE claim_id = NEW.claim_id
    ), (
        SELECT lease_until_key FROM agent_execution_dispatch_claims WHERE claim_id = NEW.claim_id
    )) OR NEW.lease_until_key <= COALESCE((
        SELECT MAX(lease_until_key) FROM agent_execution_dispatch_renewals WHERE claim_id = NEW.claim_id
    ), (
        SELECT lease_until_key FROM agent_execution_dispatch_claims WHERE claim_id = NEW.claim_id
    )) THEN RAISE(ABORT, 'Renewal must extend a live Lease') END;
END;
