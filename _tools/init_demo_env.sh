#!/usr/bin/env bash
# AMSDP demo environment initialization — M7-B0/B2.
#
# (Re)creates the ISOLATED demo stack from scratch:
#   1. Stops the demo project if running.
#   2. Starts only the demo database on its dedicated volume.
#   3. Runs alembic migrations against the demo database.
#   4. Seeds the demo database (idempotent; refreshes dates to today).
#   5. Starts the rest of the demo stack.
#
# The DEVELOPMENT stack/data are never touched by this script.
# It requires the dev stack to be DOWN (host ports overlap).
#
# Usage:
#   _tools/init_demo_env.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# Credentials are never stored in the repository.  Copy .env.example to .env
# (gitignored) and fill the values in once; this script, the other _tools/
# scripts and `docker compose` all read that single local file.
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required - set it in .env (see .env.example)}"
# Built here, never echoed: the DSN carries the password.
DEMO_DSN="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp_demo"
DEMO_LOGIN_PASSWORD="${AMSDP_DEMO_PASSWORD_RECEPTIONIST:-${AMSDP_DEMO_PASSWORD:?AMSDP_DEMO_PASSWORD_RECEPTIONIST is required - set it in .env (see .env.example)}}"

PY="${VENV_PY:-/home/shomonrobie/amsdp/.venv/bin/python}"
COMPOSE="docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml"

echo "==> [1/6] Stopping demo project (if running) ..."
$COMPOSE down >/dev/null 2>&1 || true

echo "==> [2/6] Starting demo database (dedicated volume amsdp_demo_pg_data) ..."
$COMPOSE up -d db >/dev/null
for i in $(seq 1 30); do
  docker exec amsdp_demo-db-1 pg_isready -U amsdp -d amsdp_demo >/dev/null 2>&1 && break
  sleep 2
done

echo "==> [3/6] Applying migrations to amsdp_demo ..."
(cd backend && AMSDP_DATABASE_URL="${DEMO_DSN}" \
  "$PY" -m alembic upgrade head)

echo "==> [4/6] Seeding demo data (idempotent) ..."
(cd backend && AMSDP_DATABASE_URL="${DEMO_DSN}" \
  "$PY" seed/seed_demo.py)

echo "==> [5/6] Starting full demo stack ..."
$COMPOSE up -d --build >/dev/null 2>&1

echo "==> [6/6] Verifying demo services respond ..."
sleep 6
curl -sf http://localhost:3100/ >/dev/null && echo "Frontend: http://localhost:3100 OK"
# Built here, never echoed: the payload carries the login password.  Double
# quotes are required so the variable is expanded (single quotes would send the
# literal text "${DEMO_LOGIN_PASSWORD}").
LOGIN_JSON="{\"username\":\"receptionist\",\"password\":\"${DEMO_LOGIN_PASSWORD}\"}"
curl -sf -X POST http://localhost:8110/api/v1/staff/login \
  -H 'Content-Type: application/json' \
  -d "${LOGIN_JSON}" >/dev/null \
  && echo "Identity login (receptionist) OK"

echo
echo "Demo environment ready. Frontend: http://localhost:3100"
echo "Accounts: admin/org_admin/br_admin/receptionist/doctor/assistant"
echo "(passwords come from .env — AMSDP_DEMO_PASSWORD_<USERNAME>; see .env.example)"