#!/bin/bash
set -euo pipefail

# System configuration deployment helper.
# Supports -n / --dry-run to preview unified diffs without modifying files.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR=""
cli_source=0
dry_run=0
if [ "${DRY_RUN:-0}" = "1" ] || [ "${SYSTEM_DEPLOY_DRY_RUN:-0}" = "1" ] || [ "${CHEZMOI_DRY_RUN:-0}" = "1" ]; then
  dry_run=1
fi
passthrough_args=()

while [ $# -gt 0 ]; do
  case "$1" in
    -n | --dry-run)
      dry_run=1
      passthrough_args+=("$1")
      shift
      ;;
    -S | --source)
      if [ $# -lt 2 ]; then
        echo "Error: $1 requires a directory path" >&2
        exit 1
      fi
      SOURCE_DIR="$2"
      cli_source=1
      passthrough_args+=("$1" "$2")
      shift 2
      ;;
    --source=*)
      SOURCE_DIR="${1#*=}"
      cli_source=1
      passthrough_args+=("$1")
      shift
      ;;
    -h | --help)
      echo "Usage: system-deploy.sh [OPTIONS]"
      echo ""
      echo "Deploy system-level configurations to /etc, /usr, etc."
      echo ""
      echo "Options:"
      echo "  -n, --dry-run        Preview system changes and unified diffs without modifying files"
      echo "  -S, --source PATH    Use specified chezmoi source directory"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: system-deploy.sh [-n|--dry-run] [-S|--source PATH] [-h|--help]" >&2
      exit 1
      ;;
  esac
done

if [ -n "$SOURCE_DIR" ]; then
  SOURCE_DIR="$(cd "$SOURCE_DIR" 2>/dev/null && pwd || echo "$SOURCE_DIR")"
fi

if [ -z "$SOURCE_DIR" ]; then
  if [ -n "${SYSTEM_SOURCE_DIR:-}" ] && [ -f "$SYSTEM_SOURCE_DIR/run_after_system-deploy.sh.tmpl" ]; then
    SOURCE_DIR="$SYSTEM_SOURCE_DIR"
  else
    git_worktree="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -n "$git_worktree" ] && [ -f "$git_worktree/run_after_system-deploy.sh.tmpl" ]; then
      SOURCE_DIR="$git_worktree"
    elif [ -f "$SCRIPT_DIR/../run_after_system-deploy.sh.tmpl" ]; then
      SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    elif [ -n "${SYSTEM_SOURCE_DIR:-}" ] && [ -d "$SYSTEM_SOURCE_DIR" ]; then
      SOURCE_DIR="$SYSTEM_SOURCE_DIR"
    else
      configured="$(chezmoi source-path 2>/dev/null || true)"
      if [ -n "$configured" ] && [ -f "$configured/run_after_system-deploy.sh.tmpl" ]; then
        SOURCE_DIR="$configured"
      elif [ -f "$HOME/.local/share/chezmoi/run_after_system-deploy.sh.tmpl" ]; then
        SOURCE_DIR="$HOME/.local/share/chezmoi"
      fi
    fi
  fi
fi

if [ -z "$SOURCE_DIR" ] || [ ! -f "$SOURCE_DIR/run_after_system-deploy.sh.tmpl" ]; then
  echo "Error: could not locate chezmoi source directory or run_after_system-deploy.sh.tmpl" >&2
  exit 1
fi

if [ "$cli_source" -eq 1 ]; then
  export SYSTEM_SOURCE_DIR="$SOURCE_DIR"
elif [ -z "${SYSTEM_SOURCE_DIR:-}" ]; then
  export SYSTEM_SOURCE_DIR="$SOURCE_DIR"
fi

rendered="$(chezmoi -S "$SOURCE_DIR" execute-template '{{ includeTemplate "run_after_system-deploy.sh.tmpl" . }}')"

if [ -z "$(echo "$rendered" | tr -d '[:space:]')" ]; then
  echo "System deployment is not configured for this machine profile."
  exit 0
fi

if [ "$dry_run" -eq 1 ]; then
  if ! grep -q '^# SYSTEM_DEPLOY_CAPABILITIES:.*dry-run' <<< "$rendered"; then
    echo "Error: system deployment template does not support dry-run protocol." >&2
    echo "Aborting to prevent unintentional live system modifications." >&2
    exit 1
  fi
fi

bash -s -- "${passthrough_args[@]}" <<< "$rendered"
