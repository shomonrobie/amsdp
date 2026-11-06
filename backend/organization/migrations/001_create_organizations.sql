-- 001_create_organizations.sql
-- AMSDP Organization Service — Sprint 2

CREATE TABLE IF NOT EXISTS organizations (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    code            TEXT NOT NULL UNIQUE,
    timezone        TEXT DEFAULT 'Asia/Dhaka',
    locale          TEXT DEFAULT 'bn',
    facility_type   TEXT NOT NULL,
    address         TEXT,
    config          TEXT DEFAULT '{}',
    status          TEXT DEFAULT 'active',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS branches (
    id              TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    name            TEXT NOT NULL,
    code            TEXT NOT NULL,
    address         TEXT,
    phone           TEXT,
    config          TEXT DEFAULT '{}',
    status          TEXT DEFAULT 'active',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_branches_org ON branches(organization_id);