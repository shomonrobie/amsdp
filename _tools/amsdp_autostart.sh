#!/usr/bin/env bash
# AMSDP — boot-time start + demo-data refresh.
#
# Invoked by the systemd user unit installed by _tools/install_autostart.sh
# (amsdp-autostart.service).  Safe to run by hand at any time:
#
#   _tools/amsdp_autostart.sh
#
# What it does
#   1. Waits for the Docker daemon to answer.  At boot it may still be starting,
#      and a *user* unit cannot order itself against the system docker.service,
#      so this waits instead of depending on it.
#   2. Runs `_tools/amsdp_stack.sh up`, which is idempotent: containers are
#      already brought back by their own `restart: unless-stopped` policy, so
#      this mainly waits for real readiness and prints the status table.
#   3. Re-runs the idempotent demo seed so the demo board is dated *today* and
#      every demo account's password hash matches the value in .env.  This is
#      what makes "all six users can log in" true after a reboot, not only after
#      a manual re-seed.
#
# Credentials are never printed: the DSN is built in-process and only the seed
# script's own non-secret output is shown.
#
# Exit 0 = stack ready and demo data refreshed.  Non-zero = investigate with:
#   journalctl --user -u amsdp-autostart.service -n 80 --no-pager
#
# Optional environment overrides
#   AMSDP_DOCKER_WAIT   seconds to wait for the daemon   (default: 180)
#   AMSDP_SKIP_SEED=1   start the stack, skip the seed   (default: seed runs)
#   VENV_PY             interpreter for the seed         (default: .venv/bin/python)

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

say() { printf '%s\n' "$*"; }

# Credentials come from the single gitignored .env — the same contract as
# _tools/init_demo_env.sh and docker compose itself.
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required - set it in .env (see .env.example)}"

DOCKER_WAIT="${AMSDP_DOCKER_WAIT:-180}"
PY="${VENV_PY:-$ROOT/.venv/bin/python}"

say "==> [1/3] Waiting for the Docker daemon (up to ${DOCKER_WAIT}s) ..."
deadline=$(( SECONDS + DOCKER_WAIT ))
until docker info >/dev/null 2>&1; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    say "ERROR: the Docker daemon did not become reachable within ${DOCKER_WAIT}s."
    say "       Check it with: sudo systemctl status snap.docker.dockerd"
    exit 1
  fi
  sleep 3
done
say "    daemon reachable."

say "==> [2/3] Starting / resuming the stack (idempotent, waits for readiness) ..."
"$ROOT/_tools/amsdp_stack.sh" up

say "==> [3/3] Refreshing demo data (idempotent; demo dates move to today) ..."
if [ "${AMSDP_SKIP_SEED:-0}" = "1" ]; then
  say "    skipped (AMSDP_SKIP_SEED=1)."
elif [ ! -x "$PY" ]; then
  say "    SKIPPED: no interpreter at $PY — set VENV_PY to override."
else
  # Built here, never echoed: the DSN carries the password.  Seeding goes
  # through the published DB port so it works whether or not the bridge
  # forwarding rules are healthy.
  DSN="postgresql+psycopg2://amsdp:${POSTGRES_PASSWORD}@127.0.0.1:5433/amsdp"
  ( cd "$ROOT/backend" && AMSDP_DATABASE_URL="$DSN" "$PY" seed/seed_demo.py )
fi

say ""
say "AMSDP is ready: http://localhost:3100"
say "Demo accounts: admin / org_admin / br_admin / receptionist / doctor / assistant"
say "(passwords: AMSDP_DEMO_PASSWORD_<USERNAME> in .env — never printed)"
