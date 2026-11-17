#!/usr/bin/env bash
# AMSDP — redeploy code changes: rebuild only what changed, wait for real
# readiness, then verify the running stack.
#
#   _tools/amsdp_rebuild.sh --check               # read-only: what changed, what would rebuild
#   _tools/amsdp_rebuild.sh --verify              # read-only: probe the running stack
#   _tools/amsdp_rebuild.sh                       # rebuild + recreate the services that changed
#   _tools/amsdp_rebuild.sh appointment frontend  # rebuild + recreate exactly these
#   _tools/amsdp_rebuild.sh --all                 # rebuild + recreate every image
#   _tools/amsdp_rebuild.sh --no-cache            # force a clean build (slow)
#
# Why this exists (see docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md)
#   * The source is COPYied into the images and docker-compose.yml mounts no code,
#     so `docker compose restart` restarts the OLD image.  A code change needs
#     `build` + `up -d` (recreate), which is what this script does.
#   * backend/common/ is copied into ALL eight backend images, so a change there
#     must rebuild all eight — the usual way a stale image gets "verified".
#   * `AMSDP_BUILD=1 _tools/amsdp_stack.sh up` rebuilds all ten images even for a
#     one-line change; this rebuilds the minimum set.
#
# Safety
#   * never runs `down`, never removes a volume, never re-seeds or resets the
#     database: patients, appointments and the audit trail survive;
#   * never prints .env values, the JWT secret or the database URL;
#   * read-only git only (status/diff) — nothing is staged, committed or reverted.
#
# Optional environment overrides
#   AMSDP_COMPOSE_PROJECT   compose project name       (default: amsdp)
#   AMSDP_READY_TIMEOUT     readiness timeout, seconds (default: 240)
#   AMSDP_HEALTH_INTERVAL   seconds between probes    (default: 3)

set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="${AMSDP_COMPOSE_PROJECT:-amsdp}"
READY_TIMEOUT="${AMSDP_READY_TIMEOUT:-240}"
HEALTH_INTERVAL="${AMSDP_HEALTH_INTERVAL:-3}"
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yml)
FRONTEND_URL="http://127.0.0.1:3100"

# service:host-port — must match the published ports in docker-compose.yml
BACKENDS=(
  "identity:8110"
  "organization:8111"
  "patient:8112"
  "doctor:8113"
  "scheduling:8114"
  "appointment:8115"
  "queuing:8116"
  "audit:8117"
)
ALL_BACKENDS=("${BACKENDS[@]%%:*}")
ALL_SERVICES=("db" "${ALL_BACKENDS[@]}" "frontend")

die()  { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
step() { printf '\n==> %s\n' "$*"; }

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is not installed or not on PATH"
  docker compose version >/dev/null 2>&1 || die "the docker compose v2 plugin is not available"
  docker info >/dev/null 2>&1 || die "the docker daemon is not reachable (try: sudo systemctl start docker)"
}

# Both stacks publish the same host ports, so only one may run at a time.
check_project_conflicts() {
  local running
  running="$(docker ps --filter 'label=com.docker.compose.project' \
    --format '{{.Label "com.docker.compose.project"}}' | sort -u || true)"
  if [ "$PROJECT" = "amsdp" ] && grep -qx 'amsdp_demo' <<<"$running"; then
    die "the isolated demo stack (project amsdp_demo) is running and uses the same ports. Stop it first: docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down"
  fi
  if [ "$PROJECT" != "amsdp" ] && grep -qx 'amsdp' <<<"$running"; then
    die "the development stack (project amsdp) is running and uses the same ports. Stop it first: docker compose -p amsdp -f docker-compose.yml down"
  fi
}

# ---------------------------------------------------------------- change detection
changed_paths() {
  {
    git status --porcelain --untracked-files=all 2>/dev/null | cut -c4-
    git diff --name-only HEAD 2>/dev/null || true
  } | sed '/^$/d' | sort -u
}

# Map one path to the services whose image must be rebuilt.
services_for_path() {
  local p="$1"
  case "$p" in
    frontend/*)             printf 'frontend\n' ;;
    backend/common/*)       printf '%s\n' "${ALL_BACKENDS[@]}" ;;
    backend/appointment/*)  printf 'appointment\n' ;;
    backend/identity/*)     printf 'identity\n' ;;
    backend/organization/*) printf 'organization\n' ;;
    backend/patient/*)      printf 'patient\n' ;;
    backend/doctor/*)       printf 'doctor\n' ;;
    backend/scheduling/*)   printf 'scheduling\n' ;;
    backend/queuing/*)      printf 'queuing\n' ;;
    backend/audit/*)        printf 'audit\n' ;;
    *) : ;;   # docs, tests, _tools, compose: no image rebuild
  esac
}

detect_services() {
  local p
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    services_for_path "$p"
  done < <(changed_paths) | sed '/^$/d' | sort -u
}

# Prints a human summary to stderr and the detected service list to stdout, so a
# caller can do: list="$(show_changes)".
show_changes() {
  local files services
  files="$(changed_paths | wc -l | tr -d ' ')"
  services="$(detect_services)"
  {
    step "Uncommitted changes: ${files} file(s) in this tree"
    if [ -n "$services" ]; then
      printf '  images that carry them:\n'
      printf '%s\n' "$services" | sed 's/^/    - /'
    else
      printf '  no service source changed — nothing to rebuild\n'
    fi
    printf '  (docs, tests, _tools and compose changes alter no image;\n'
    printf '   a compose/env change only needs: %s up -d)\n' "${COMPOSE[*]}"
  } >&2
  [ -n "$services" ] && printf '%s\n' "$services"
  return 0
}

# ------------------------------------------------------------------- readiness wait
svc_state() {
  "${COMPOSE[@]}" ps --format '{{.Service}} {{.State}} {{.Health}}' 2>/dev/null \
    | awk -v s="$1" '$1==s {print $2" "$3}' || true
}

http_code() { curl -s -o /dev/null -m 3 -w '%{http_code}' "$1" 2>/dev/null || echo 000; }

port_of() {
  local entry
  for entry in "${BACKENDS[@]}"; do
    [ "${entry%%:*}" = "$1" ] && { printf '%s' "${entry##*:}"; return 0; }
  done
  return 0
}

probe_service() {
  case "$1" in
    db)       "${COMPOSE[@]}" exec -T db pg_isready -U amsdp -d amsdp >/dev/null 2>&1 ;;
    frontend) [ "$(http_code "$FRONTEND_URL/")" = "200" ] ;;
    *)        [ "$(http_code "http://127.0.0.1:$(port_of "$1")/health/ready")" = "200" ] ;;
  esac
}

wait_ready() {
  local deadline failures svc
  step "Waiting for readiness (timeout ${READY_TIMEOUT}s)"
  deadline=$(( $(date +%s) + READY_TIMEOUT ))
  while :; do
    failures=""
    for svc in "${ALL_SERVICES[@]}"; do
      probe_service "$svc" || failures+="${svc} "
    done
    if [ -z "$failures" ]; then
      printf '  every service is ready\n'
      return 0
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      printf '\nERROR: not ready within %ss. Not ready: %s\n' "$READY_TIMEOUT" "$failures" >&2
      "${COMPOSE[@]}" ps >&2 || true
      for svc in $failures; do
        printf -- '\n--- %s (last 25 log lines) ---\n' "$svc" >&2
        "${COMPOSE[@]}" logs --tail=25 "$svc" >&2 || true
      done
      return 1
    fi
    sleep "$HEALTH_INTERVAL"
  done
}


# ------------------------------------------------------------------------- verify
verify() {
  local rc=0 svc code state health result
  step "Verifying the running stack (read-only)"
  printf '  %-14s %-9s %-8s %s\n' SERVICE STATE HEALTH PROBE
  for svc in "${ALL_SERVICES[@]}"; do
    state=""; health=""
    read -r state health <<<"$(svc_state "$svc")" || true
    if probe_service "$svc"; then result=ok; else result=FAILED; rc=1; fi
    printf '  %-14s %-9s %-8s %s\n' "$svc" "${state:--}" "${health:--}" "$result"
  done

  step "Deployed-code checks (through the published API)"
  # 401 without a token proves the route exists in the running image. It is the
  # appointment service's newest route, so it is the cheapest "is my code live?"
  # probe that needs no credentials.
  code="$(http_code "http://127.0.0.1:$(port_of appointment)/api/v1/appointments/list")"
  if [ "$code" = "401" ]; then
    printf '  appointments/list without a token: HTTP %s (route deployed, auth enforced)  ok\n' "$code"
  else
    printf '  appointments/list without a token: HTTP %s (expected 401 — stale image?)  FAILED\n' "$code"
    rc=1
  fi
  code="$(http_code "$FRONTEND_URL/appointments")"
  printf '  %s/appointments: HTTP %s (200/307 = page present, 5xx = broken build)\n' "$FRONTEND_URL" "$code"
  [ "$code" = "000" ] && rc=1

  step "Access"
  printf '  Application:  %s\n' "$FRONTEND_URL"
  printf '  Database:     PostgreSQL in container %s-db-1 (host port 5433)\n' "$PROJECT"
  [ "$rc" -eq 0 ] || printf '\nOne or more checks FAILED (see above).\n' >&2
  return "$rc"
}



# ---------------------------------------------------------------------- rebuild
rebuild() {
  local -a targets=("$@") flags=()
  [ "${NO_CACHE:-0}" = "1" ] && flags+=(--no-cache)
  step "Rebuilding: ${targets[*]}"
  "${COMPOSE[@]}" build "${flags[@]}" "${targets[@]}"
  step "Recreating only those containers (volumes and data are kept)"
  "${COMPOSE[@]}" up -d --no-deps "${targets[@]}"
  wait_ready
  verify
}

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; }

main() {
  local mode="apply" arg detected
  local -a targets=()
  NO_CACHE=0
  for arg in "$@"; do
    case "$arg" in
      --check)        mode="check" ;;
      --verify)       mode="verify" ;;
      --all)          mode="all" ;;
      --no-cache)     NO_CACHE=1 ;;
      help|-h|--help) usage; return 0 ;;
      -*)             die "unknown option '$arg' (try: $0 help)" ;;
      *)              targets+=("$arg") ;;
    esac
  done

  require_docker
  check_project_conflicts

  case "$mode" in
    check)
      show_changes >/dev/null
      printf '\n'
      "${COMPOSE[@]}" ps
      printf '\nApply with:  %s\n' "$0"
      ;;
    verify)
      verify
      ;;
    all)
      rebuild "${ALL_BACKENDS[@]}" frontend
      ;;
    apply)
      if [ "${#targets[@]}" -gt 0 ]; then
        rebuild "${targets[@]}"
      else
        detected="$(show_changes)"
        if [ -z "$detected" ]; then
          step "Nothing changed — verifying the running stack instead"
          verify
        else
          local -a list
          readarray -t list <<<"$detected"
          rebuild "${list[@]}"
        fi
      fi
      ;;
  esac
}

main "$@"
