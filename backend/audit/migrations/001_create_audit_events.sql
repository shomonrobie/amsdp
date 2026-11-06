-- 001_create_audit_events.sql
CREATE TABLE IF NOT EXISTS audit_events (
    event_id        TEXT PRIMARY KEY,
    service         TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    action          TEXT NOT NULL,
    target_type     TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    actor_id        TEXT NOT NULL,
    actor_role      TEXT NOT NULL,
    before          TEXT DEFAULT '{}',
    after           TEXT DEFAULT '{}',
    reason          TEXT DEFAULT '',
    timestamp       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_events(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_events(organization_id);