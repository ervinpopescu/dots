#!/bin/bash
set -euo pipefail

# ==============================================================================
# Helper to retire the Solux user-level systemd preview daemon.
# To be executed only during rollout AFTER static assets are deployed to
# /var/www/solux and Nginx has been reloaded.
# ==============================================================================

echo "Retiring Solux user systemd service (transition to static Nginx)..."

if systemctl --user is-active --quiet solux.service 2>/dev/null; then
  echo "Stopping solux.service..."
  systemctl --user stop solux.service
fi

if systemctl --user is-enabled --quiet solux.service 2>/dev/null; then
  echo "Disabling solux.service..."
  systemctl --user disable solux.service
fi

TARGET_UNIT="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/solux.service"
if [ -f "$TARGET_UNIT" ]; then
  echo "Removing $TARGET_UNIT..."
  rm -f "$TARGET_UNIT"
fi

systemctl --user daemon-reload 2>/dev/null || true
echo "Solux user service successfully retired."
