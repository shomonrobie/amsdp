#!/usr/bin/env bash
# AMSDP — prove every demo account can sign in, through the frontend proxy.
#
#   _tools/verify_demo_login.sh
#
# Asks the SAME endpoint the browser uses (http://localhost:3100/api/v1/staff/login)
# for all six demo accounts and prints OK / FAIL per account.  Usernames, roles
# and HTTP status are shown; passwords and tokens never are.
#
# Exit 0 = all six signed in.  1 = at least one failed (read the reason printed).
#
# Optional environment overrides
#   AMSDP_BASE_URL   base URL to test   (default: http://localhost:3100)

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

BASE="${AMSDP_BASE_URL:-http://localhost:3100}"
USERS=(admin org_admin br_admin receptionist doctor assistant)

# The response body carries the session token — keep it in a private temp file
# and delete it on exit.
body_file="$(umask 077; mktemp)"
trap 'rm -f "$body_file"' EXIT

printf '  %-14s %-6s %s\n' ACCOUNT RESULT DETAIL
fail=0

for u in "${USERS[@]}"; do
  var="AMSDP_DEMO_PASSWORD_$(printf '%s' "$u" | tr '[:lower:]' '[:upper:]')"
  pw="${!var:-}"
  if [ -z "$pw" ]; then
    printf '  %-14s %-6s %s\n' "$u" FAIL "no $var in .env"
    fail=1
    continue
  fi

  # Built in-process; never echoed.  Double quotes are required so the variable
  # expands (single quotes would send the literal text).
  payload="{\"username\":\"${u}\",\"password\":\"${pw}\"}"

  code="$(curl -s -m 20 -o "$body_file" -w '%{http_code}' \
            -X POST "$BASE/api/v1/staff/login" \
            -H 'Content-Type: application/json' \
            -d "$payload" 2>/dev/null || echo 000)"

  token="$(sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$body_file" | head -1)"
  role="$(sed -n 's/.*"role"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$body_file" | head -1)"

  if [ "$code" = "200" ] && [ -n "$token" ]; then
    printf '  %-14s %-6s %s\n' "$u" OK "HTTP 200, role=${role:-?}"
  else
    detail="HTTP ${code}"
    if [ -n "$role" ]; then detail="${detail}, role=${role}"; fi
    case "$code" in
      000) detail="${detail} — no response (is the frontend up on ${BASE}?)" ;;
      401) detail="${detail} — credential rejected" ;;
      502|503|504) detail="${detail} — backend unreachable through the proxy" ;;
    esac
    printf '  %-14s %-6s %s\n' "$u" FAIL "$detail"
    fail=1
  fi
done

echo
if [ "$fail" -eq 0 ]; then
  echo "All ${#USERS[@]} demo accounts signed in through ${BASE}."
else
  echo "At least one demo account failed. Re-seed with: _tools/amsdp_autostart.sh"
fi
exit "$fail"
