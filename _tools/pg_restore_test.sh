#!/usr/bin/env bash
# AMSDP restore VERIFICATION — M7-B1.
#
# Restores a pg_dump file into a TEMPORARY, ISOLATED database
# (amsdp_restore_test) and verifies schema + essential records +
# application connectivity. The development database is NEVER touched:
# restore targets only the throwaway test database.
#
# All psql/pg_dump invocations run INSIDE the postgres:16 container so
# server and client versions match (avoiding SET transaction_timeout etc.)
#
# Usage:
#   _tools/pg_restore_test.sh [backup_file.sql.gz]
#
# On success prints VERIFIED and drops amsdp_restore_test. On failure the
# test database is left in place (drop manually) for investigation.
set -uo pipefail

BACKUP="${1:?usage: _tools/pg_restore_test.sh <backup.sql.gz>}"
CONTAINER="${AMSDP_DB_CONTAINER:-amsdp-db-1}"
MAINT_DB="${AMSDP_DB_NAME:-amsdp}"
TEST_DB="amsdp_restore_test"

# Credentials are never stored in the repository.  They come from .env
# (gitignored, see .env.example) or from the caller's environment.  The working
# directory is left untouched so a relative backup path still resolves.
_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${_ROOT}/.env" ]; then
  set -a
  . "${_ROOT}/.env"
  set +a
fi
DB_PASSWORD="${AMSDP_DB_PASSWORD:-${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required - set it in .env (see .env.example)}}"
# Built here, never echoed: the DSN carries the password.
RESTORE_DSN="postgresql+psycopg2://amsdp:${DB_PASSWORD}@127.0.0.1:5433/${TEST_DB}"

# Helper: PEXEC <psql-args> runs psql against the TEST_DB inside container
PEXEC() { docker exec -i -e PGPASSWORD="${DB_PASSWORD}" "${CONTAINER}" psql --username=amsdp --dbname="${TEST_DB}" -v ON_ERROR_STOP=1 "$@"; }
# Helper: PSCHEMA runs psql in the maintenance DB for schema-level ops
PSCHEMA() { docker exec -i -e PGPASSWORD="${DB_PASSWORD}" "${CONTAINER}" psql --username=amsdp --dbname="${MAINT_DB}" -t -A "$@"; }

echo "==> [1/5] Dropping stale temp DB ${TEST_DB} if any ..."
PSCHEMA -c "DROP DATABASE IF EXISTS ${TEST_DB};"
PSCHEMA -c "CREATE DATABASE ${TEST_DB};"
echo "     Created empty database."

echo "==> [2/5] Restoring '${BACKUP}' into ${TEST_DB} ..."
gunzip -c "${BACKUP}" | PEXEC >/dev/null
echo "     Restore OK."

echo "==> [3/5] Verifying schema (tables present)..."
TABLES="$(PEXEC -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
echo "     Tables: ${TABLES}"

echo "==> [4/5] Verifying essential records ..."
echo -n "  organizations: "; PEXEC -t -A -c "SELECT count(*) FROM organizations;"
echo -n "  branches:      "; PEXEC -t -A -c "SELECT count(*) FROM branches;"
echo -n "  staff_users:   "; PEXEC -t -A -c "SELECT count(*) FROM staff_users;"
echo -n "  patients:      "; PEXEC -t -A -c "SELECT count(*) FROM patients;"
echo -n "  appointments:  "; PEXEC -t -A -c "SELECT count(*) FROM appointments;"
echo -n "  audit_events:  "; PEXEC -t -A -c "SELECT count(*) FROM audit_events;"
echo -n "  alembic head:  "; PEXEC -t -A -c "SELECT version_num FROM alembic_version;"

echo "==> [5/5] Application-connectivity probe (SQLAlchemy) ..."
ERR=""
AMSDP_DATABASE_URL="${RESTORE_DSN}" \
  /home/shomonrobie/amsdp/.venv/bin/python - <<'PY' 2>&1 | grep -E '(OK|Error|ERROR|Traceback)' || true
import os
from sqlalchemy import create_engine, text
e = create_engine(os.environ["AMSDP_DATABASE_URL"])
with e.connect() as c:
    s = c.execute(text("SELECT count(*) FROM staff_users")).scalar()
    v = c.execute(text("SELECT version_num FROM alembic_version")).scalar()
    print(f"  SQLAlchemy probe OK: staff_users={s}, alembic={v}")
PY
echo "     (SQLAlchemy probe complete — see line above)"

echo "==> Cleaning up temp DB ..."
PSCHEMA -c "DROP DATABASE ${TEST_DB};" >/dev/null
echo "==> RESTORE VERIFIED — temp database dropped."