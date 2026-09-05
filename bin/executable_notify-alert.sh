#!/bin/bash
# Multi-channel notification dispatcher: phone push (ntfy), email (SMTP), desktop.
# Configuration is read from $XDG_CONFIG_HOME/notify/config.env (~/.config/notify/config.env)

set -eo pipefail

CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/notify/config.env"

# Defaults
NOTIFY_CHANNELS="${NOTIFY_CHANNELS:-ntfy}"
NTFY_TOPIC="${NTFY_TOPIC:-aslan-cluster-alerts}"
NOTIFY_EMAIL_TO="${NOTIFY_EMAIL_TO:-ervin.popescu10@gmail.com}"
SMTP_URL="${SMTP_URL:-smtp://smtp.gmail.com:587}"
SMTP_USER="${SMTP_USER:-ervin.popescu10@gmail.com}"
SMTP_PASS="${SMTP_PASS:-}"
SMTP_FROM="${SMTP_FROM:-ervin.popescu10@gmail.com}"

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

TITLE="System Notification"
MESSAGE=""
PRIORITY="high"
TAGS="warning"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--title)
      TITLE="$2"
      shift 2
      ;;
    -m|--message)
      MESSAGE="$2"
      shift 2
      ;;
    -p|--priority)
      PRIORITY="$2"
      shift 2
      ;;
    --tags)
      TAGS="$2"
      shift 2
      ;;
    *)
      if [[ -z "$MESSAGE" ]]; then
        MESSAGE="$1"
      fi
      shift
      ;;
  esac
done

# If message is still empty, read from stdin
if [[ -z "$MESSAGE" ]]; then
  MESSAGE=$(cat)
fi

if [[ -z "$MESSAGE" ]]; then
  echo "notify-alert: empty message" >&2
  exit 1
fi

send_ntfy() {
  if [[ -z "$NTFY_TOPIC" ]]; then
    echo "notify-alert: NTFY_TOPIC not configured" >&2
    return 1
  fi
  curl -fsSL \
    -H "Title: $TITLE" \
    -H "Priority: $PRIORITY" \
    -H "Tags: $TAGS" \
    -d "$MESSAGE" \
    "https://ntfy.sh/$NTFY_TOPIC" >/dev/null || {
      echo "notify-alert: failed to send ntfy notification" >&2
      return 1
    }
}

send_email() {
  if [[ -z "$SMTP_PASS" ]]; then
    echo "notify-alert: SMTP_PASS is empty; skipping direct email" >&2
    return 0
  fi

  local email_data
  email_data=$(cat <<EOF
From: ${SMTP_FROM:-$SMTP_USER}
To: $NOTIFY_EMAIL_TO
Subject: $TITLE
Date: $(date -R)
Content-Type: text/plain; charset=utf-8

$MESSAGE
EOF
)

  echo "$email_data" | curl -fsSL --ssl-reqd \
    --url "$SMTP_URL" \
    --user "$SMTP_USER:$SMTP_PASS" \
    --mail-from "${SMTP_FROM:-$SMTP_USER}" \
    --mail-rcpt "$NOTIFY_EMAIL_TO" \
    --upload-file - >/dev/null || {
      echo "notify-alert: failed to send email via $SMTP_URL" >&2
      return 1
    }
}

send_desktop() {
  if [[ -n "$DISPLAY" || -n "$WAYLAND_DISPLAY" ]]; then
    if command -v notify-send >/dev/null 2>&1; then
      notify-send -u critical "$TITLE" "$MESSAGE" 2>/dev/null || true
    fi
    if [[ -x "$HOME/bin/alert.sh" ]]; then
      "$HOME/bin/alert.sh" 2>/dev/null || true
    fi
  fi
}

for channel in $NOTIFY_CHANNELS; do
  case "$channel" in
    ntfy)
      send_ntfy || true
      ;;
    email)
      send_email || true
      ;;
    desktop)
      send_desktop || true
      ;;
    *)
      echo "notify-alert: unknown channel '$channel'" >&2
      ;;
  esac
done
