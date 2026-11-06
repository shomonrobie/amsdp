-- 001_create_queue_entries.sql
CREATE TABLE IF NOT EXISTS queue_entries (
    queue_entry_id  TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    branch_id       TEXT NOT NULL,
    doctor_id       TEXT NOT NULL,
    date            TEXT NOT NULL,
    position        INTEGER NOT NULL,
    token           TEXT NOT NULL,
    patient_id      TEXT NOT NULL,
    appointment_id  TEXT,
    entry_source    TEXT DEFAULT 'appointment',
    status          TEXT DEFAULT 'waiting',
    status_history  TEXT DEFAULT '[]',
    notes           TEXT,
    added_by        TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_queue_doctor_date ON queue_entries(doctor_id, date);
CREATE INDEX IF NOT EXISTS idx_queue_org ON queue_entries(organization_id);