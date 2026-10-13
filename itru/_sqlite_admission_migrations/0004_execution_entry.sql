-- AIO-058 private permanent Dispatch-wide execution Entry, schema version 4.
-- Entry is neither invocation evidence nor a Result; it is never reset.
CREATE TABLE agent_execution_entries (
    authorization_domain_id TEXT COLLATE BINARY NOT NULL CHECK (authorization_domain_id <> ''),
    issuer_kind TEXT COLLATE BINARY NOT NULL CHECK (issuer_kind IN ('human', 'policy')),
    issuer_id TEXT COLLATE BINARY NOT NULL CHECK (issuer_id <> ''),
    grant_id TEXT COLLATE BINARY NOT NULL CHECK (grant_id <> ''),
    claim_id TEXT COLLATE BINARY NOT NULL CHECK (length(claim_id)=64 AND claim_id NOT GLOB '*[^0-9a-f]*'),
    executor_instance_id TEXT COLLATE BINARY NOT NULL CHECK (length(executor_instance_id)=64 AND executor_instance_id NOT GLOB '*[^0-9a-f]*'),
    lease_generation INTEGER NOT NULL CHECK (lease_generation > 0),
    entry_time TEXT COLLATE BINARY NOT NULL CHECK (length(entry_time)=27),
    entry_time_key INTEGER NOT NULL CHECK (entry_time_key BETWEEN 0 AND 315537897599999999),
    PRIMARY KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id),
    FOREIGN KEY (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        REFERENCES agent_execution_dispatch_intents (authorization_domain_id, issuer_kind, issuer_id, grant_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (claim_id, authorization_domain_id, issuer_kind, issuer_id, grant_id, executor_instance_id, lease_generation)
        REFERENCES agent_execution_dispatch_claims (claim_id, authorization_domain_id, issuer_kind, issuer_id, grant_id, executor_instance_id, lease_generation)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT, WITHOUT ROWID;

CREATE TRIGGER agent_execution_entries_no_update BEFORE UPDATE ON agent_execution_entries
BEGIN SELECT RAISE(ABORT, 'Execution Entries are immutable'); END;
CREATE TRIGGER agent_execution_entries_no_delete BEFORE DELETE ON agent_execution_entries
BEGIN SELECT RAISE(ABORT, 'Execution Entries are immutable'); END;
CREATE TRIGGER agent_execution_entries_no_duplicate BEFORE INSERT ON agent_execution_entries
WHEN EXISTS (SELECT 1 FROM agent_execution_entries WHERE
    authorization_domain_id=NEW.authorization_domain_id AND issuer_kind=NEW.issuer_kind
    AND issuer_id=NEW.issuer_id AND grant_id=NEW.grant_id)
BEGIN SELECT RAISE(ABORT, 'Dispatch has permanently entered'); END;
CREATE TRIGGER agent_execution_entries_operational_insert BEFORE INSERT ON agent_execution_entries
WHEN NOT EXISTS (SELECT 1 FROM admission_ledger_metadata WHERE singleton=1
    AND activation_state='active' AND migration_state='clean' AND schema_version=4)
BEGIN SELECT RAISE(ABORT, 'Entry requires active clean v4 state'); END;
CREATE TRIGGER agent_execution_entries_history_insert_guard BEFORE INSERT ON agent_execution_entries
BEGIN
    SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM agent_execution_dispatch_claims c
        WHERE c.claim_id=NEW.claim_id AND c.authorization_domain_id=NEW.authorization_domain_id
        AND c.issuer_kind=NEW.issuer_kind AND c.issuer_id=NEW.issuer_id AND c.grant_id=NEW.grant_id
        AND c.executor_instance_id=NEW.executor_instance_id AND c.lease_generation=NEW.lease_generation
        AND c.lease_generation=(SELECT MAX(h.lease_generation) FROM agent_execution_dispatch_claims h
            WHERE h.authorization_domain_id=NEW.authorization_domain_id AND h.issuer_kind=NEW.issuer_kind
            AND h.issuer_id=NEW.issuer_id AND h.grant_id=NEW.grant_id)
        AND c.acquired_at_key<=NEW.entry_time_key
        AND NEW.entry_time_key<COALESCE((SELECT MAX(r.lease_until_key)
            FROM agent_execution_dispatch_renewals r WHERE r.claim_id=c.claim_id),c.lease_until_key))
        OR EXISTS (SELECT 1 FROM legacy_admission_markers WHERE authorization_domain_id=NEW.authorization_domain_id
            AND issuer_kind=NEW.issuer_kind AND issuer_id=NEW.issuer_id AND grant_id=NEW.grant_id)
        OR EXISTS (SELECT 1 FROM agent_execution_grant_revocations WHERE authorization_domain_id=NEW.authorization_domain_id
            AND issuer_kind=NEW.issuer_kind AND issuer_id=NEW.issuer_id AND grant_id=NEW.grant_id)
        THEN RAISE(ABORT, 'Entry requires exact current unrevoked live Claim') END;
    SELECT CASE WHEN NEW.entry_time_key<(SELECT last_decision_time_key FROM admission_ledger_metadata WHERE singleton=1)
        OR NEW.entry_time_key<(SELECT decision_time_key FROM agent_execution_dispatch_admissions
            WHERE authorization_domain_id=NEW.authorization_domain_id AND issuer_kind=NEW.issuer_kind
            AND issuer_id=NEW.issuer_id AND grant_id=NEW.grant_id)
        THEN RAISE(ABORT, 'Entry time regresses') END;
END;

DROP TRIGGER agent_execution_dispatch_intents_operational_insert;
CREATE TRIGGER agent_execution_dispatch_intents_operational_insert BEFORE INSERT ON agent_execution_dispatch_intents
WHEN NOT EXISTS (SELECT 1 FROM admission_ledger_metadata WHERE singleton=1
    AND activation_state='active' AND migration_state='clean' AND schema_version=4)
BEGIN SELECT RAISE(ABORT, 'Intent insertion requires active clean v4 state'); END;
DROP TRIGGER agent_execution_dispatch_claims_operational_insert;
CREATE TRIGGER agent_execution_dispatch_claims_operational_insert BEFORE INSERT ON agent_execution_dispatch_claims
WHEN NOT EXISTS (SELECT 1 FROM admission_ledger_metadata WHERE singleton=1
    AND activation_state='active' AND migration_state='clean' AND schema_version=4)
BEGIN SELECT RAISE(ABORT, 'Claim insertion requires active clean v4 state'); END;
DROP TRIGGER agent_execution_dispatch_renewals_operational_insert;
CREATE TRIGGER agent_execution_dispatch_renewals_operational_insert BEFORE INSERT ON agent_execution_dispatch_renewals
WHEN NOT EXISTS (SELECT 1 FROM admission_ledger_metadata WHERE singleton=1
    AND activation_state='active' AND migration_state='clean' AND schema_version=4)
BEGIN SELECT RAISE(ABORT, 'Renewal insertion requires active clean v4 state'); END;
