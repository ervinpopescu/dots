#!/bin/bash
# Systemd failure handler: formats a service failure report and sends it via notify-alert.sh

set -eo pipefail

UNIT="${1:-unknown.service}"
HOST="$(uname -n)"
DATE="$(date '+%Y-%m-%d %H:%M:%S %Z')"

STATUS_LOG=$(systemctl --user status "$UNIT" --no-pager 2>&1 || true)
JOURNAL_LOG=$(journalctl --user -u "$UNIT" -n 25 --no-pager 2>&1 || true)

BODY=$(cat <<EOF
[ALERT] Service '$UNIT' failed on $HOST!
Time: $DATE
Unit: $UNIT

=== Service Status ===
$STATUS_LOG

=== Last 25 Journal Entries ===
$JOURNAL_LOG
EOF
)

# Dispatch notification
NOTIFY_BIN="${HOME}/bin/notify-alert.sh"
if [[ ! -x "$NOTIFY_BIN" ]]; then
  # Fallback to PATH lookup
  NOTIFY_BIN=$(command -v notify-alert.sh || echo "")
fi

if [[ -n "$NOTIFY_BIN" && -x "$NOTIFY_BIN" ]]; then
  "$NOTIFY_BIN" \
    --title "[$HOST] $UNIT failed" \
    --priority "urgent" \
    --tags "warning,skull,kubernetes" \
    --message "$BODY"
else
  echo "systemd-notify-failure: notify-alert.sh not found in PATH or ~/bin" >&2
  exit 1
fi
