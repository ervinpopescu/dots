#!/usr/bin/env bash
set -euo pipefail

: "${HOME:?HOME must be set}"
: "${HM_RENAME_NOREPLACE_BIN:?HM_RENAME_NOREPLACE_BIN must be set by the Nix wrapper}"

mode=manual
old_generation=
new_generation=
if (($# == 0)); then
  :
elif (($# == 3 || $# == 4)) && [[ $1 == --forward || $1 == --rollback ]]; then
  mode=${1#--}
  old_generation=$2
  new_generation=$3
  managed_generation=${4:-$new_generation}
else
  echo "usage: hm-restore-backups [--forward|--rollback OLD_GENERATION NEW_GENERATION [MANAGED_GENERATION]]" >&2
  exit 2
fi

if [[ $mode == forward ]]; then
  echo "Backup restoration skipped for forward activation."
  exit 0
fi
if [[ $mode == rollback && $old_generation == "$new_generation" ]]; then
  echo "Backup restoration skipped because the generation is unchanged."
  exit 0
fi

managed_files=
if [[ $mode == rollback ]]; then
  if [[ -z ${managed_generation:-} ]] ||
    ! managed_files=$(readlink -e -- "$managed_generation/home-files") ||
    [[ ! -d $managed_files ]]; then
    echo "Cannot determine the rollback generation's managed paths; retaining backups." >&2
    exit 1
  fi
fi

state_root=${XDG_STATE_HOME:-"$HOME/.local/state"}/home-manager/collision-backups
if [[ ! -d "$state_root" ]]; then
  exit 0
fi

restored_total=0
pending_total=0
error_total=0
session_pending=0

restore_record() {
  local record_state=$1 target=$2 backup=$3 expected_identity=$4
  local actual_identity status relative managed_target

  case "$target" in
  "$HOME"/*) ;;
  *)
    echo "Skipping manifest target outside HOME: $target" >&2
    session_pending=1
    ((error_total += 1))
    return
    ;;
  esac
  case "$backup" in
  "$target".*) ;;
  *)
    echo "Skipping invalid backup path for $target: $backup" >&2
    session_pending=1
    ((error_total += 1))
    return
    ;;
  esac

  if [[ ! -e "$backup" && ! -L "$backup" ]]; then
    return
  fi

  if [[ -n "$expected_identity" ]]; then
    actual_identity=$(stat -c '%d:%i' -- "$backup")
    if [[ $actual_identity != "$expected_identity" ]]; then
      if [[ $record_state == committed ]]; then
        echo "Keeping backup whose identity no longer matches its committed record: $backup" >&2
        session_pending=1
        ((pending_total += 1))
        ((error_total += 1))
      else
        echo "Keeping ambiguous prepared backup with a different identity: $backup" >&2
        session_pending=1
        ((pending_total += 1))
        ((error_total += 1))
      fi
      return
    fi
  fi

  if [[ $mode == rollback ]]; then
    relative=${target#"$HOME"/}
    managed_target="$managed_files/$relative"
    if [[ -e $managed_target || -L $managed_target ]]; then
      printf 'Keeping backup; rollback generation manages target: %s\n' "$backup"
      session_pending=1
      ((pending_total += 1))
      return
    fi
  fi

  if [[ -e "$target" || -L "$target" ]]; then
    printf 'Keeping backup; target remains managed or exists: %s\n' "$backup"
    session_pending=1
    ((pending_total += 1))
    return
  fi

  mkdir -p -- "$(dirname -- "$target")"
  if "$HM_RENAME_NOREPLACE_BIN" "$backup" "$target"; then
    printf 'Restored %s\n' "$target"
    ((restored_total += 1))
  else
    status=$?
    session_pending=1
    ((pending_total += 1))
    if ((status == 3)); then
      printf 'Keeping backup; target appeared during restore: %s\n' "$backup"
    else
      printf 'Keeping backup; atomic restore failed: %s\n' "$backup" >&2
      ((error_total += 1))
    fi
  fi
}

declare -a sessions=() session_orders=()
while IFS= read -r -d '' discovered_session; do
  discovered_order=0
  if [[ -f "$discovered_session/order" ]]; then
    discovered_order=$(<"$discovered_session/order")
    if [[ ! $discovered_order =~ ^[0-9]+$ ]] ||
      ((discovered_order > 9223372036854775807)); then
      echo "Invalid backup session order: $discovered_session/order" >&2
      ((error_total += 1))
      continue
    fi
  fi

  insert_index=${#sessions[@]}
  while ((insert_index > 0)) &&
    ((session_orders[insert_index - 1] < discovered_order)); do
    sessions[insert_index]=${sessions[insert_index - 1]}
    session_orders[insert_index]=${session_orders[insert_index - 1]}
    insert_index=$((insert_index - 1))
  done
  sessions[insert_index]=$discovered_session
  session_orders[insert_index]=$discovered_order
done < <(
  find "$state_root" -mindepth 1 -maxdepth 1 -type d \
    ! -name generations ! -name link-guards -print0
)

for session in "${sessions[@]}"; do
  exec {session_lock_fd}>"$session/.lock"
  flock "$session_lock_fd"

  manifest="$session/manifest"
  if [[ ! -f "$manifest" ]]; then
    flock -u "$session_lock_fd"
    exec {session_lock_fd}>&-
    continue
  fi
  session_status=
  if [[ -f "$session/status" ]]; then
    session_status=$(<"$session/status")
  fi
  if [[ $session_status == restored ]]; then
    flock -u "$session_lock_fd"
    exec {session_lock_fd}>&-
    continue
  fi

  session_pending=0
  if [[ -f "$session/manifest-format" ]]; then
    if [[ $(<"$session/manifest-format") != 2 ]]; then
      echo "Unsupported backup manifest format: $session/manifest-format" >&2
      ((error_total += 1))
      flock -u "$session_lock_fd"
      exec {session_lock_fd}>&-
      continue
    fi

    declare -a record_states=() record_targets=() record_backups=() record_identities=()
    declare -A record_indexes=()
    malformed=0
    while IFS= read -r -d '' record_state; do
      if ! IFS= read -r -d '' target ||
        ! IFS= read -r -d '' backup ||
        ! IFS= read -r -d '' identity; then
        malformed=1
        break
      fi
      case "$record_state" in
      prepared | committed | aborted) ;;
      *)
        malformed=1
        break
        ;;
      esac
      if [[ ${record_indexes["$backup"]+present} ]]; then
        index=${record_indexes["$backup"]}
      else
        index=${#record_states[@]}
        record_indexes["$backup"]=$index
      fi
      record_states[index]=$record_state
      record_targets[index]=$target
      record_backups[index]=$backup
      record_identities[index]=$identity
    done <"$manifest"

    if ((malformed)); then
      echo "Malformed backup manifest: $manifest" >&2
      session_pending=1
      ((error_total += 1))
    else
      for index in "${!record_states[@]}"; do
        [[ ${record_states[index]} != aborted ]] || continue
        restore_record \
          "${record_states[index]}" \
          "${record_targets[index]}" \
          "${record_backups[index]}" \
          "${record_identities[index]}"
      done
    fi
    unset record_states record_targets record_backups record_identities record_indexes
  else
    while IFS= read -r -d '' target && IFS= read -r -d '' backup; do
      restore_record committed "$target" "$backup" ""
    done <"$manifest"
  fi

  if ((session_pending)); then
    printf 'pending\n' >"$session/status"
  else
    printf 'restored\n' >"$session/status"
  fi
  flock -u "$session_lock_fd"
  exec {session_lock_fd}>&-
done

printf 'Backup restoration: %d restored, %d retained.\n' "$restored_total" "$pending_total"
((error_total == 0))
