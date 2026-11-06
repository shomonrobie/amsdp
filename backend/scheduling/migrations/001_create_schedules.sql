-- 001_create_schedules.sql
CREATE TABLE IF NOT EXISTS schedules (
    id                  TEXT PRIMARY KEY,
    doctor_id           TEXT NOT NULL,
    organization_id     TEXT NOT NULL,
    branch_id           TEXT NOT NULL,
    appointment_model   TEXT DEFAULT 'time_slot',
    effective_from      TEXT,
    effective_to        TEXT,
    slot_templates      TEXT DEFAULT '[]',
    status              TEXT DEFAULT 'active',
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_schedules_doctor ON schedules(doctor_id);
CREATE INDEX IF NOT EXISTS idx_schedules_org ON schedules(organization_id);