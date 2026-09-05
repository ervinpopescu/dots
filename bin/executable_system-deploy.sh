#!/bin/bash
set -euo pipefail

# System configuration deployment helper.
# Supports -n / --dry-run to preview unified diffs without modifying files.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR=""

if [ -n "${SYSTEM_SOURCE_DIR:-}" ] && [ -f "$SYSTEM_SOURCE_DIR/run_after_system-deploy.sh.tmpl" ]; then
  SOURCE_DIR="$SYSTEM_SOURCE_DIR"
elif [ -f "$SCRIPT_DIR/../run_after_system-deploy.sh.tmpl" ]; then
  SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -n "${SYSTEM_SOURCE_DIR:-}" ] && [ -d "$SYSTEM_SOURCE_DIR" ]; then
  SOURCE_DIR="$SYSTEM_SOURCE_DIR"
else
  SOURCE_DIR="$(chezmoi source-path 2>/dev/null || true)"
  if [ -z "$SOURCE_DIR" ] || [ ! -f "$SOURCE_DIR/run_after_system-deploy.sh.tmpl" ]; then
    if [ -f "$HOME/.local/share/chezmoi/run_after_system-deploy.sh.tmpl" ]; then
      SOURCE_DIR="$HOME/.local/share/chezmoi"
    fi
  fi
fi

if [ -z "$SOURCE_DIR" ] || [ ! -f "$SOURCE_DIR/run_after_system-deploy.sh.tmpl" ]; then
  echo "Error: could not locate chezmoi source directory or run_after_system-deploy.sh.tmpl" >&2
  exit 1
fi

rendered="$(chezmoi -S "$SOURCE_DIR" execute-template '{{ includeTemplate "run_after_system-deploy.sh.tmpl" . }}')"

if [ -z "$(echo "$rendered" | tr -d '[:space:]')" ]; then
  echo "System deployment is not configured for this machine profile."
  exit 0
fi

bash -s -- "$@" <<< "$rendered"
