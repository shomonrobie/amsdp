-- 001_create_doctors.sql
CREATE TABLE IF NOT EXISTS doctors (
    id                  TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL,
    branch_ids          TEXT DEFAULT '[]',
    name                TEXT NOT NULL,
    mobile              TEXT NOT NULL,
    speciality          TEXT DEFAULT '',
    qualification       TEXT DEFAULT '',
    registration_number TEXT,
    consultation_fee    REAL,
    locale              TEXT DEFAULT 'bn',
    status              TEXT DEFAULT 'active',
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doctors_org ON doctors(organization_id);