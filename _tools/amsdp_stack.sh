#!/usr/bin/env bash
# AMSDP — one command to start, restart, stop or inspect the full local stack.
#
#   _tools/amsdp_stack.sh              # start / resume everything (default: up)
#   _tools/amsdp_stack.sh up           # start / resume everything  (idempotent)
#   _tools/amsdp_stack.sh restart      # graceful restart of every service
#   _tools/amsdp_stack.sh stop         # stop the stack, keep containers + data
#   _tools/amsdp_stack.sh status       # service state, health and HTTP probes
#   _tools/amsdp_stack.sh logs [svc]   # follow logs (all services or one)
#   _tools/amsdp_stack.sh help
#
# What it does
#   * uses the existing docker-compose.yml (PostgreSQL + 8 backend services +
#     frontend) — no second orchestration mechanism, no new deployment platform;
#   * `up` is safe to run repeatedly: running services are left alone, stopped
#     ones are started, nothing is duplicated (compose is the single owner);
#   * waits for real readiness — every service's /health/ready probe and the
#     frontend — and prints a status table only after that, so "success" is never
#     reported for a half-started stack;
#   * never runs `down`, never removes a volume, never re-seeds or resets the
#     database: patient/appointment data survives every restart;
#   * never prints environment variables, the JWT secret or the database URL.
#
# Optional environment overrides
#   AMSDP_COMPOSE_PROJECT   compose project name        (default: amsdp)
#   AMSDP_READY_TIMEOUT     readiness timeout, seconds   (default: 180)
#   AMSDP_BUILD=1           rebuild images before start  (default: build only if
#                           an image is missing, which compose does itself)
#   AMSDP_HEALTH_INTERVAL   seconds between probes       (default: 3)

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="${AMSDP_COMPOSE_PROJECT:-amsdp}"
READY_TIMEOUT="${AMSDP_READY_TIMEOUT:-180}"
HEALTH_INTERVAL="${AMSDP_HEALTH_INTERVAL:-3}"
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yml)
FRONTEND_URL="http://127.0.0.1:3100"
FRONTEND_HEALTH_URL="${FRONTEND_URL}/"

# service:host-port — the published ports from docker-compose.yml
BACKEND_SERVICES=(
  "identity:8110"
  "organization:8111"
  "patient:8112"
  "doctor:8113"
  "scheduling:8114"
  "appointment:8115"
  "queuing:8116"
  "audit:8117"
)
ALL_SERVICES=(db "${BACKEND_SERVICES[@]%%:*}" frontend)

die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is not installed or not on PATH"
  docker compose version >/dev/null 2>&1 || die "the docker compose v2 plugin is not available"
  docker info >/dev/null 2>&1 || die "the docker daemon is not reachable (is it running? try: sudo systemctl start docker)"
}

# The demo project re-uses the same host ports, so both stacks cannot run at once.
check_project_conflicts() {
  local running
  running="$(docker ps --filter 'label=com.docker.compose.project' \
    --format '{{.Label "com.docker.compose.project"}}' | sort -u || true)"

  if [ "$PROJECT" = "amsdp" ] && grep -qx 'amsdp_demo' <<<"$running"; then
    die "the isolated demo stack (project amsdp_demo) is running and uses the same host ports.
       Stop it first:  docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down"
  fi
  if [ "$PROJECT" != "amsdp" ] && grep -qx 'amsdp' <<<"$running"; then
    die "the development stack (project amsdp) is running and uses the same host ports.
       Stop it first:  docker compose -p amsdp stop"
  fi
}


# ---------------------------------------------------------------- health probes
http_ok() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS -m 3 -o /dev/null "$url" 2>/dev/null
  else
    python3 - "$url" <<'PY' 2>/dev/null
import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as r:
        sys.exit(0 if 200 <= r.status < 400 else 1)
except Exception:
    sys.exit(1)
PY
  fi
}

db_ok() {
  docker compose -p "$PROJECT" -f docker-compose.yml exec -T db \
    pg_isready -U amsdp -d amsdp >/dev/null 2>&1
}

# Prints one line per service: SERVICE<TAB>STATE<TAB>HEALTH
service_table() {
  "${COMPOSE[@]}" ps --all --format '{{.Service}}\t{{.State}}\t{{.Health}}' 2>/dev/null || true
}

# STATE<TAB>HEALTH for one service; "missing" when the container does not exist.
service_state() {
  local svc="$1" row
  row="$(service_table | awk -F'\t' -v s="$svc" '$1==s{print $2"\t"($3==""?"-":$3); exit}')"
  [ -z "$row" ] && row=$'missing\t-'
  printf '%s' "$row"
}

probe_failures() {
  local failures=()
  db_ok || failures+=("db: pg_isready failed")

  local entry svc port
  for entry in "${BACKEND_SERVICES[@]}"; do
    svc="${entry%%:*}"
    port="${entry##*:}"
    http_ok "http://127.0.0.1:${port}/health/ready" \
      || failures+=("${svc}: http://127.0.0.1:${port}/health/ready not ready")
  done

  http_ok "$FRONTEND_HEALTH_URL" || failures+=("frontend: ${FRONTEND_HEALTH_URL} not reachable")
  printf '%s\n' "${failures[@]+"${failures[@]}"}"
}


wait_ready() {
  local deadline=$(( $(date +%s) + READY_TIMEOUT ))
  local attempt=0

  step "Waiting for every service to become ready (timeout ${READY_TIMEOUT}s)"
  while :; do
    attempt=$((attempt + 1))
    local failures
    failures="$(probe_failures)"

    if [ -z "$failures" ]; then
      say "    all services ready after ${attempt} probe(s)"
      return 0
    fi

    if [ "$(date +%s)" -ge "$deadline" ]; then
      printf '\nERROR: not every service became ready within %ss.\n\n' "$READY_TIMEOUT" >&2
      printf 'Service state:\n' >&2
      service_table | sed 's/^/  /' >&2
      printf '\nUnhealthy probes:\n' >&2
      printf '%s\n' "$failures" | sed 's/^/  - /' >&2
      printf '\nLast log lines of the failing services:\n' >&2
      local line svc
      while IFS= read -r line; do
        [ -z "$line" ] && continue
        svc="${line%%:*}"
        printf -- '\n--- %s ---\n' "$svc" >&2
        "${COMPOSE[@]}" logs --tail=25 "$svc" >&2 || true
      done <<<"$failures"
      printf '\nThe stack is NOT ready. Investigate with:  %s logs <service>\n' "$0" >&2
      return 1
    fi

    sleep "$HEALTH_INTERVAL"
  done
}

print_status() {
  step "Service status (compose project: ${PROJECT})"
  printf '  %-14s %-9s %-9s %s\n' SERVICE STATE HEALTH PROBE
  local svc state health entry port probe
  for svc in "${ALL_SERVICES[@]}"; do
    IFS=$'\t' read -r state health <<<"$(service_state "$svc")"
    case "$svc" in
      db) probe="$(db_ok && echo ok || echo FAILED)" ;;
      frontend) probe="$(http_ok "$FRONTEND_HEALTH_URL" && echo ok || echo FAILED)" ;;
      *)
        port=""
        for entry in "${BACKEND_SERVICES[@]}"; do
          [ "${entry%%:*}" = "$svc" ] && port="${entry##*:}"
        done
        if [ -n "$port" ]; then
          probe="$(http_ok "http://127.0.0.1:${port}/health/ready" && echo ok || echo FAILED)"
        else
          probe="-"
        fi
        ;;
    esac
    printf '  %-14s %-9s %-9s %s\n' "$svc" "$state" "${health:--}" "$probe"
  done

  step "Access"
  say "  Application (frontend):  ${FRONTEND_URL}"
  say "  Backend API services:    8 services on host ports 8110-8117, reached through the frontend proxy (/api/v1/*)"
  say "  Database:                PostgreSQL in container ${PROJECT}-db-1 (host port 5433, volume ${PROJECT}_amsdp_pg_data)"
}


# ------------------------------------------------------------------- commands
cmd_up() {
  require_docker
  check_project_conflicts
  step "Starting / resuming the full AMSDP stack (project: ${PROJECT})"
  if [ "${AMSDP_BUILD:-0}" = "1" ]; then
    "${COMPOSE[@]}" up -d --build
  else
    "${COMPOSE[@]}" up -d
  fi
  wait_ready
  print_status
}

cmd_restart() {
  require_docker
  check_project_conflicts
  step "Gracefully restarting the full AMSDP stack (project: ${PROJECT})"
  # Make sure every container exists, then restart in place: volumes, data and
  # configuration are kept, and no service is duplicated.
  "${COMPOSE[@]}" up -d
  "${COMPOSE[@]}" restart
  wait_ready
  print_status
}

cmd_stop() {
  require_docker
  step "Stopping the AMSDP stack (containers and volumes are kept)"
  "${COMPOSE[@]}" stop
  say "    stopped. Data is preserved; start again with:  $0 up"
}

cmd_status() {
  require_docker
  print_status
}

cmd_logs() {
  require_docker
  "${COMPOSE[@]}" logs --tail=60 -f "$@"
}

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
}

main() {
  local command="${1:-up}"
  [ $# -gt 0 ] && shift || true
  case "$command" in
    up|start)         cmd_up ;;
    restart)          cmd_restart ;;
    stop)             cmd_stop ;;
    status|ps)        cmd_status ;;
    logs)             cmd_logs "$@" ;;
    help|-h|--help)   usage ;;
    *) die "unknown command '${command}' (try: $0 help)" ;;
  esac
}

main "$@"
