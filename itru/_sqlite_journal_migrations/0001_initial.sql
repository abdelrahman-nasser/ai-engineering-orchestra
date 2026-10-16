CREATE TABLE journal_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton=1),
    journal_id TEXT COLLATE BINARY NOT NULL CHECK (length(journal_id)>0),
    authorization_domain_id TEXT COLLATE BINARY NOT NULL CHECK (length(authorization_domain_id)>0),
    ledger_instance_id TEXT COLLATE BINARY NOT NULL CHECK (length(ledger_instance_id)>0),
    domain_generation TEXT COLLATE BINARY NOT NULL CHECK (length(domain_generation)>0),
    schema_version INTEGER NOT NULL CHECK (schema_version=1),
    migration_sha256 TEXT COLLATE BINARY NOT NULL CHECK (length(migration_sha256)=64)
) STRICT;

CREATE TABLE journal_entries (
    sequence INTEGER PRIMARY KEY CHECK (sequence>0),
    subject_key TEXT COLLATE BINARY NOT NULL,
    event_kind TEXT COLLATE BINARY NOT NULL CHECK (event_kind IN ('entry_observed','result_observed')),
    recorded_at TEXT COLLATE BINARY NOT NULL CHECK (length(recorded_at)=27),
    record_json TEXT COLLATE BINARY NOT NULL CHECK (length(record_json)<=1048576),
    UNIQUE (subject_key,event_kind)
) STRICT;

CREATE TRIGGER journal_metadata_no_update BEFORE UPDATE ON journal_metadata
BEGIN SELECT RAISE(ABORT,'Journal metadata is immutable'); END;

CREATE TRIGGER journal_metadata_no_delete BEFORE DELETE ON journal_metadata
BEGIN SELECT RAISE(ABORT,'Journal metadata is immutable'); END;

CREATE TRIGGER journal_metadata_no_duplicate BEFORE INSERT ON journal_metadata
WHEN EXISTS (SELECT 1 FROM journal_metadata)
BEGIN SELECT RAISE(ABORT,'Journal metadata already exists'); END;

CREATE TRIGGER journal_entries_no_update BEFORE UPDATE ON journal_entries
BEGIN SELECT RAISE(ABORT,'Journal entries are immutable'); END;

CREATE TRIGGER journal_entries_no_delete BEFORE DELETE ON journal_entries
BEGIN SELECT RAISE(ABORT,'Journal entries are immutable'); END;

CREATE TRIGGER journal_entries_no_duplicate BEFORE INSERT ON journal_entries
WHEN EXISTS (SELECT 1 FROM journal_entries WHERE sequence=NEW.sequence
    OR (subject_key=NEW.subject_key AND event_kind=NEW.event_kind))
BEGIN SELECT RAISE(ABORT,'Journal fact already exists'); END;

CREATE TRIGGER journal_entries_contiguous BEFORE INSERT ON journal_entries
WHEN NEW.sequence!=COALESCE((SELECT MAX(sequence) FROM journal_entries),0)+1
BEGIN SELECT RAISE(ABORT,'Journal sequence must be contiguous'); END;

CREATE TRIGGER journal_entries_result_parent BEFORE INSERT ON journal_entries
WHEN NEW.event_kind='result_observed' AND NOT EXISTS
    (SELECT 1 FROM journal_entries WHERE subject_key=NEW.subject_key AND event_kind='entry_observed')
BEGIN SELECT RAISE(ABORT,'Result observation requires Entry observation'); END;
