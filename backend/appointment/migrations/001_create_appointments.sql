-- 001_create_appointments.sql
CREATE TABLE IF NOT EXISTS appointments (
    id                  TEXT PRIMARY KEY,
    organization_id     TEXT NOT NULL,
    branch_id           TEXT NOT NULL,
    patient_id          TEXT NOT NULL,
    doctor_id           TEXT NOT NULL,
    appointment_date    TEXT NOT NULL,
    start_time          TEXT,
    serial_number       INTEGER,
    appointment_type    TEXT DEFAULT 'scheduled',
    status              TEXT DEFAULT 'scheduled',
    status_history      TEXT DEFAULT '[]',
    token_number        TEXT,
    notes               TEXT,
    created_by          TEXT,
    rescheduled_from    TEXT,
    rescheduled_to      TEXT,
    reschedule_reason   TEXT,
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);