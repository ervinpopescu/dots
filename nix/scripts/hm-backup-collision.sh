#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: hm-backup-collision TARGET" >&2
  exit 2
}

append_record() {
  local state=$1 target_path=$2 backup_path=$3 identity=$4
  if ! printf '%s\0%s\0%s\0%s\0' \
    "$state" "$target_path" "$backup_path" "$identity" >>"$manifest" ||
    ! sync -f -- "$manifest"; then
    echo "could not durably record $state backup transaction for $target_path" >&2
    return 1
  fi
}

[[ $# -eq 1 ]] || usage
target=$1
: "${HOME:?HOME must be set}"
: "${HM_RENAME_NOREPLACE_BIN:?HM_RENAME_NOREPLACE_BIN must be set by the Nix wrapper}"

case "$target" in
"$HOME"/*) ;;
*)
  echo "refusing to back up path outside HOME: $target" >&2
  exit 1
  ;;
esac

state_root=${XDG_STATE_HOME:-"$HOME/.local/state"}/home-manager/collision-backups
umask 077
if [[ -n ${HM_BACKUP_SESSION:-} ]]; then
  session=$HM_BACKUP_SESSION
  backup_id=${HM_BACKUP_ID:?HM_BACKUP_ID must accompany HM_BACKUP_SESSION}
else
  mkdir -p -- "$state_root"
  session=$(mktemp -d "$state_root/hm-auto-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
  backup_id=${session##*/}
fi

case "$backup_id" in
*[!A-Za-z0-9._-]* | "")
  echo "invalid backup identifier: $backup_id" >&2
  exit 1
  ;;
esac

activation_id=${HM_LINK_ACTIVATION_ID:-hm-link-$$-$RANDOM-$RANDOM}
case "$activation_id" in
*[!A-Za-z0-9._-]* | "")
  echo "invalid link activation identifier: $activation_id" >&2
  exit 1
  ;;
esac

mkdir -p -- "$session"
exec {session_lock_fd}>"$session/.lock"
flock "$session_lock_fd"
session_order="$session/order"
if [[ ! -f "$session_order" ]]; then
  exec {order_lock_fd}>"$state_root/.order.lock"
  flock "$order_lock_fd"
  if [[ ! -f "$session_order" ]]; then
    order_counter_file="$state_root/next-session-order"
    order_counter=0
    if [[ -f "$order_counter_file" ]]; then
      order_counter=$(<"$order_counter_file")
      if [[ ! $order_counter =~ ^[0-9]+$ ]] ||
        ((order_counter >= 9223372036854775806)); then
        echo "invalid backup session order counter: $order_counter_file" >&2
        exit 1
      fi
    fi
    session_order_value=$((order_counter + 1))
    order_counter_temporary="$state_root/.next-session-order.$$"
    printf '%d\n' "$session_order_value" >"$order_counter_temporary"
    sync -f -- "$order_counter_temporary"
    mv -f -- "$order_counter_temporary" "$order_counter_file"
    sync -f -- "$state_root"

    session_order_temporary="$session/.order.$$"
    printf '%d\n' "$session_order_value" >"$session_order_temporary"
    sync -f -- "$session_order_temporary"
    mv -f -- "$session_order_temporary" "$session_order"
    sync -f -- "$session"
  fi
  flock -u "$order_lock_fd"
  exec {order_lock_fd}>&-
fi

manifest="$session/manifest"
manifest_format="$session/manifest-format"
touch -- "$manifest"
if [[ ! -e "$manifest_format" ]]; then
  printf '2\n' >"$manifest_format"
  sync -f -- "$manifest_format"
elif [[ $(<"$manifest_format") != 2 ]]; then
  echo "unsupported backup manifest format: $manifest_format" >&2
  exit 1
fi
printf 'active\n' >"$session/status"

backup="$target.$backup_id"
if [[ ! -e "$target" && ! -L "$target" ]]; then
  echo "collision target does not exist: $target" >&2
  exit 1
fi
if [[ -e "$backup" || -L "$backup" ]]; then
  echo "backup already exists: $backup" >&2
  exit 1
fi

source_identity=$(stat -c '%d:%i' -- "$target")
append_record prepared "$target" "$backup" "$source_identity"

if "$HM_RENAME_NOREPLACE_BIN" "$target" "$backup"; then
  backup_identity=$(stat -c '%d:%i' -- "$backup")
  append_record committed "$target" "$backup" "$backup_identity"
  if [[ -n ${HM_BACKUP_RESULT_FILE:-} ]]; then
    printf '%s\0%s\0%s\0' "$session" "$backup" "$backup_identity" \
      >"$HM_BACKUP_RESULT_FILE"
    sync -f -- "$HM_BACKUP_RESULT_FILE"
  fi
  guard_key=$(printf '%s' "$target" | sha256sum)
  guard_key=${guard_key%% *}
  for guard_root in \
    "$session/link-guards" \
    "$state_root/link-guards/$activation_id"; do
    mkdir -p -- "$guard_root"
    guard_temporary="$guard_root/.$guard_key.$$"
    printf '%s\0' "$target" >"$guard_temporary"
    sync -f -- "$guard_temporary"
    mv -f -- "$guard_temporary" "$guard_root/$guard_key"
    sync -f -- "$guard_root"
  done
else
  status=$?
  append_record aborted "$target" "$backup" "$source_identity"
  if ((status == 3)); then
    echo "backup appeared before collision could be moved: $backup" >&2
  else
    echo "could not move collision to backup: $target" >&2
  fi
  exit 1
fi

printf 'Backed up %s -> %s\n' "$target" "$backup"
