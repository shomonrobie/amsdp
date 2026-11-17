#!/usr/bin/env bash
# AMSDP PostgreSQL backup — M7-B1.
#
# Dumps the DEVELOPMENT database (amsdp on host port 5433) to
# a compressed, timestamped file. Safe to run while the dev stack is up.
#
# Uses the pg_dump INSIDE the postgres:16 container so the dumper version
# always matches the server version (a newer host pg_dump would emit
# SET transaction_timeout / other options the server does not understand).
#
# Usage:
#   _tools/pg_backup.sh [output_dir]   (default: ./backups)
#
# The dump is a --clean/--if-exists plain SQL dump so it can be restored
# into an EMPTY or REPLACED target database with psql.
set -euo pipefail

CONTAINER="${AMSDP_DB_CONTAINER:-amsdp-db-1}"
DB_NAME="${AMSDP_DB_NAME:-amsdp}"
BACKUP_DIR="${1:-backups}"

# Credentials are never stored in the repository.  They come from .env
# (gitignored, see .env.example) or from the caller's environment.  The working
# directory is left untouched so a relative output directory still resolves.
_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "${_ROOT}/.env" ]; then
  set -a
  . "${_ROOT}/.env"
  set +a
fi
DB_PASSWORD="${AMSDP_DB_PASSWORD:-${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required - set it in .env (see .env.example)}}"

mkdir -p "${BACKUP_DIR}"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/amsdp_${DB_NAME}_${TS}.sql.gz"

echo "==> Backing up '${DB_NAME}' via container ${CONTAINER} ..."
docker exec -e PGPASSWORD="${DB_PASSWORD}" "${CONTAINER}" \
  pg_dump --username=amsdp --dbname="${DB_NAME}" \
  --clean --if-exists --no-owner --no-privileges \
  | gzip > "${OUT}"

echo "==> Backup written: ${OUT}"
gzip -l "${OUT}"
echo "==> Row-count spot check (via container):"
docker exec -e PGPASSWORD="${DB_PASSWORD}" "${CONTAINER}" \
  psql --username=amsdp --dbname="${DB_NAME}" -t -A -c \
  "SELECT 'organizations='||count(*) FROM organizations UNION ALL SELECT 'patients='||count(*) FROM patients;"