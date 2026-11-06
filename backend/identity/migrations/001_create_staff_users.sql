-- 001_create_staff_users.sql
-- AMSDP Identity & Access Service — Sprint 1
-- Database-per-service model (D6): separate logical DB per service.

CREATE TABLE IF NOT EXISTS staff_users (
    id              TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    branch_id       TEXT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    role            TEXT NOT NULL,
    email           TEXT,
    mobile          TEXT,
    locale          TEXT DEFAULT 'en',
    status          TEXT DEFAULT 'active',
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_staff_users_org ON staff_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_staff_users_role ON staff_users(role);