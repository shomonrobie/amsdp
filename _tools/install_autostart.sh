#!/usr/bin/env bash
# AMSDP — install the boot-time auto-start unit (systemd *user* manager).
#
#   _tools/install_autostart.sh               # install, enable, start now
#   _tools/install_autostart.sh --status      # show the unit state
#   _tools/install_autostart.sh --uninstall   # disable and remove it
#
# Why a *user* unit rather than a system one
#   * it needs no root, so the install is reproducible on any account;
#   * this account already has lingering enabled (Linger=yes), which is what
#     makes the user manager start at boot without anyone logging in;
#   * the unit cannot declare `Requires=docker.service` — ordering a user unit
#     against a system unit is not supported — so _tools/amsdp_autostart.sh
#     waits for the daemon itself before touching the stack.
#
# Division of responsibility
#   * container-level auto-restart (a crash, or the whole host rebooting) is
#     handled by `restart: unless-stopped` in docker-compose.yml;
#   * this unit adds the readiness gate and the demo-data refresh on top.
#   Either one alone keeps the demo up; together they also keep the demo data
#   current.

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

UNIT_NAME="amsdp-autostart.service"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_PATH="$UNIT_DIR/$UNIT_NAME"

case "${1:-}" in
  --uninstall)
    systemctl --user disable --now "$UNIT_NAME" 2>/dev/null || true
    rm -f "$UNIT_PATH"
    systemctl --user daemon-reload
    echo "Removed $UNIT_NAME (container restart policies are unaffected)."
    exit 0
    ;;
  --status)
    systemctl --user --no-pager status "$UNIT_NAME" || true
    exit 0
    ;;
  "" ) : ;;
  *)   echo "unknown option '$1' (try: --status, --uninstall)" >&2; exit 2 ;;
esac

command -v systemctl >/dev/null 2>&1 || { echo "systemd is required" >&2; exit 1; }
[ -x "$ROOT/_tools/amsdp_autostart.sh" ] || chmod +x "$ROOT/_tools/amsdp_autostart.sh"

mkdir -p "$UNIT_DIR"
cat > "$UNIT_PATH" <<EOF
[Unit]
Description=AMSDP local stack — auto-start with demo data
Documentation=file://${ROOT}/README.md
After=network-online.target
Wants=network-online.target
# Retry forever: at boot the daemon may legitimately be slower than one attempt.
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${ROOT}
ExecStart=${ROOT}/_tools/amsdp_autostart.sh
TimeoutStartSec=900
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$UNIT_NAME"

# Lingering is what lets the user manager run at boot with nobody logged in.
if command -v loginctl >/dev/null 2>&1; then
  linger="$(loginctl show-user "$USER" -p Linger --value 2>/dev/null || echo unknown)"
  if [ "$linger" != "yes" ]; then
    loginctl enable-linger "$USER" 2>/dev/null \
      || echo "WARNING: could not enable lingering; the unit will only run while you are logged in." >&2
  fi
fi

echo "Installed $UNIT_PATH"
echo "Starting it now (this brings the stack up and refreshes the demo data) ..."
systemctl --user start "$UNIT_NAME"
systemctl --user --no-pager status "$UNIT_NAME" || true
