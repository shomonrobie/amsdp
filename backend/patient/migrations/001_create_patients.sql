-- 001_create_patients.sql
CREATE TABLE IF NOT EXISTS patients (
    id              TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    name            TEXT NOT NULL,
    mobile          TEXT NOT NULL,
    date_of_birth   TEXT,
    sex             TEXT,
    address         TEXT,
    national_id     TEXT,
    status          TEXT DEFAULT 'active',
    merged_into     TEXT,
    merge_reason    TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_patients_org ON patients(organization_id);
CREATE INDEX IF NOT EXISTS idx_patients_mobile ON patients(organization_id, mobile);