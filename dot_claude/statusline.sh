#!/usr/bin/env bash

input=$(cat)

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // "unknown"')

# --- Rate limits ---
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# --- Context window ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# --- Session start time (approximate via transcript path mtime) ---
transcript=$(echo "$input" | jq -r '.transcript_path // empty')
session_time=""
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  start_epoch=$(stat -c %Y "$transcript" 2>/dev/null)
  if [ -n "$start_epoch" ]; then
    now_epoch=$(date +%s)
    elapsed=$(( now_epoch - start_epoch ))
    h=$(( elapsed / 3600 ))
    m=$(( (elapsed % 3600) / 60 ))
    if [ "$h" -gt 0 ]; then
      session_time=$(printf "%dh%02dm" "$h" "$m")
    else
      session_time=$(printf "%dm" "$m")
    fi
  fi
fi

# --- ANSI colors (dimmed-friendly) ---
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Foreground colors
CYAN='\033[36m'
YELLOW='\033[33m'
GREEN='\033[32m'
RED='\033[31m'
MAGENTA='\033[35m'
BLUE='\033[34m'
WHITE='\033[37m'

# --- Git branch + changes ---
cwd=$(echo "$input" | jq -r '.cwd // "."')
git_info=""
if git -C "$cwd" rev-parse --is-inside-work-tree --no-optional-locks &>/dev/null 2>&1; then
  branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
  shortstat=$(git -C "$cwd" --no-optional-locks diff --shortstat 2>/dev/null)
  insertions=0
  deletions=0
  if [ -n "$shortstat" ]; then
    ins_match=$(echo "$shortstat" | grep -oP '\d+(?= insertion)')
    del_match=$(echo "$shortstat" | grep -oP '\d+(?= deletion)')
    [ -n "$ins_match" ] && insertions=$ins_match
    [ -n "$del_match" ] && deletions=$del_match
  fi
  if [ "$insertions" -gt 0 ] || [ "$deletions" -gt 0 ]; then
    diff_suffix=" $(printf "${GREEN}+%d${RESET} ${RED}-%d${RESET}" "$insertions" "$deletions")"
    git_info="${branch}${diff_suffix}"
  else
    git_info="${branch}"
  fi
fi

# --- Path in fish format (abbreviate home dirs and middle components) ---
fish_path() {
  local p="$1"
  # Replace home dir with ~
  p="${p/#$HOME/\~}"
  # Split on / and abbreviate all but last component to first char
  IFS='/' read -ra parts <<< "$p"
  local count="${#parts[@]}"
  local result=""
  for (( i=0; i<count-1; i++ )); do
    seg="${parts[$i]}"
    if [ -z "$seg" ]; then
      result="${result}/"
    elif [ "$seg" = "~" ]; then
      # shellcheck disable=SC2088
      result="~/"
    else
      result="${result}${seg:0:1}/"
    fi
  done
  result="${result}${parts[$((count-1))]}"
  echo "$result"
}

short_path=$(fish_path "$cwd")

# Build output parts
parts=()

# Model
parts+=("$(printf "${BOLD}${CYAN}%s${RESET}" "$model")")

# 5h usage
if [ -n "$five_pct" ]; then
  pct_int=$(printf "%.0f" "$five_pct")
  if [ "$pct_int" -ge 80 ]; then
    color="$RED"
  elif [ "$pct_int" -ge 50 ]; then
    color="$YELLOW"
  else
    color="$GREEN"
  fi
  parts+=("$(printf "5h:${color}%s%%${RESET}" "$pct_int")")
fi

# 7d usage
if [ -n "$week_pct" ]; then
  pct_int=$(printf "%.0f" "$week_pct")
  if [ "$pct_int" -ge 80 ]; then
    color="$RED"
  elif [ "$pct_int" -ge 50 ]; then
    color="$YELLOW"
  else
    color="$GREEN"
  fi
  parts+=("$(printf "7d:${color}%s%%${RESET}" "$pct_int")")
fi

# Context window
if [ -n "$used_pct" ]; then
  pct_int=$(printf "%.0f" "$used_pct")
  if [ "$pct_int" -ge 80 ]; then
    color="$RED"
  elif [ "$pct_int" -ge 50 ]; then
    color="$YELLOW"
  else
    color="$GREEN"
  fi
  parts+=("$(printf "ctx:${color}%s%%%s${RESET}" "$pct_int" " used")")
fi

# Session cost in dollars (Claude Code estimate; may differ from billing due to cache discounts)
cost_raw=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')
if [ -n "$cost_raw" ]; then
  cost=$(printf '$%.4f' "$cost_raw")
  parts+=("$(printf "${DIM}${WHITE}%s${RESET}" "$cost")")
fi

# Session time
if [ -n "$session_time" ]; then
  parts+=("$(printf "${DIM}${WHITE}%s${RESET}" "$session_time")")
fi

# Git info
if [ -n "$git_info" ]; then
  parts+=("$(printf "${MAGENTA}%s${RESET}" "$git_info")")
fi

# Path
parts+=("$(printf "${BLUE}%s${RESET}" "$short_path")")

# Join with separator
sep="$(printf ' %b|%b ' "${DIM}" "${RESET}")"
result=""
for part in "${parts[@]}"; do
  if [ -z "$result" ]; then
    result="$part"
  else
    result="${result}${sep}${part}"
  fi
done

printf "%b\n" "$result"
