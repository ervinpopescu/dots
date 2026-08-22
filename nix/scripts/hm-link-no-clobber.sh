#!/usr/bin/env bash
set -euo pipefail

: "${HM_BACKUP_COMMAND:?HM_BACKUP_COMMAND must be set by the Nix wrapper}"
: "${HM_RENAME_NOREPLACE_BIN:?HM_RENAME_NOREPLACE_BIN must be set by the Nix wrapper}"
: "${HM_REAL_LN:?HM_REAL_LN must be set by the Nix wrapper}"
: "${HM_REAL_RM:?HM_REAL_RM must be set by the Nix wrapper}"
: "${HM_STORE_DIR:?HM_STORE_DIR must be set by the Nix wrapper}"
: "${HM_LINK_ACTIVATION_ID:?HM_LINK_ACTIVATION_ID must be set by the Nix wrapper}"

case "$HM_LINK_ACTIVATION_ID" in
*[!A-Za-z0-9._-]* | "")
  echo "invalid link activation identifier: $HM_LINK_ACTIVATION_ID" >&2
  exit 1
  ;;
esac

HM_STORE_DIR=$(readlink -f -- "$HM_STORE_DIR")

force=0
symbolic=0
target_directory=
expect_target_directory=0
options=()
operands=()

for argument in "$@"; do
  if ((expect_target_directory)); then
    target_directory=$argument
    expect_target_directory=0
    continue
  fi
  case "$argument" in
  --force)
    force=1
    ;;
  --symbolic)
    symbolic=1
    options+=("$argument")
    ;;
  --target-directory)
    expect_target_directory=1
    ;;
  --target-directory=*)
    target_directory=${argument#*=}
    ;;
  --)
    options+=("$argument")
    ;;
  -*)
    short=${argument#-}
    [[ $short == *f* ]] && force=1
    [[ $short == *s* ]] && symbolic=1
    short=${short//f/}
    [[ -n $short ]] && options+=("-$short")
    [[ $short == *t* ]] && expect_target_directory=1
    ;;
  *)
    operands+=("$argument")
    ;;
  esac
done

if ((!force || !symbolic)); then
  exec "$HM_REAL_LN" "$@"
fi

activation_guard_path() {
  local target=$1 guard_key
  guard_key=$(printf '%s' "$target" | sha256sum)
  guard_key=${guard_key%% *}
  printf '%s/%s/%s\n' \
    "${XDG_STATE_HOME:-$HOME/.local/state}/home-manager/collision-backups/link-guards" \
    "$HM_LINK_ACTIVATION_ID" "$guard_key"
}

target_was_backed() {
  local target=$1 guard_path guard_target
  if [[ -n ${HM_BACKUP_SESSION:-} ]]; then
    guard_path="$HM_BACKUP_SESSION/link-guards/${2:-}"
    if [[ -f $guard_path ]]; then
      IFS= read -r -d '' guard_target <"$guard_path" || true
      [[ $guard_target == "$target" ]] && return 0
    fi
  fi
  guard_path=$(activation_guard_path "$target")
  if [[ -f $guard_path ]]; then
    IFS= read -r -d '' guard_target <"$guard_path" || true
    [[ $guard_target == "$target" ]] && return 0
  fi
  return 1
}

clear_activation_guard() {
  rm -f -- "$(activation_guard_path "$1")"
}

link_test_checkpoint() {
  local name=$1 checkpoint=${HM_LINK_TEST_CHECKPOINT_DIR:-}
  [[ -n $checkpoint ]] || return 0
  : >"$checkpoint/$name.ready"
  while [[ ! -e $checkpoint/$name.continue ]]; do
    sleep 0.01
  done
}

backup_target() {
  local target=$1 result status
  local -a fields=()

  result=$(mktemp)
  if HM_BACKUP_RESULT_FILE="$result" "$HM_BACKUP_COMMAND" "$target"; then
    status=0
  else
    status=$?
  fi
  if ((status != 0)); then
    "$HM_REAL_RM" -f -- "$result"
    return "$status"
  fi
  mapfile -d '' -t fields <"$result"
  "$HM_REAL_RM" -f -- "$result"
  if ((${#fields[@]} != 3)); then
    echo "backup command did not return a complete transaction result" >&2
    return 1
  fi
  backed_path=${fields[1]}
  backed_identity=${fields[2]}
}

restore_recorded_backup() {
  local target=$1
  if [[ -e $target || -L $target ]]; then
    return 1
  fi
  "$HM_RENAME_NOREPLACE_BIN" "$backed_path" "$target"
}

safe_link() {
  local source=$1 target=$2 current guard_key status
  guard_key=$(printf '%s' "$target" | sha256sum)
  guard_key=${guard_key%% *}
  if target_was_backed "$target" "$guard_key"; then
    if [[ -e $target || -L $target ]]; then
      clear_activation_guard "$target"
      printf 'Refusing to overwrite link target recreated after backup: %s\n' "$target" >&2
      return 1
    fi
    link_test_checkpoint backed-target-absent
    if "$HM_REAL_LN" -Ts -- "$source" "$target"; then
      status=0
    else
      status=$?
    fi
    clear_activation_guard "$target"
    return "$status"
  fi
  if [[ -L $target ]]; then
    current=$(readlink -- "$target")
    case "$current" in
    "$HM_STORE_DIR"/*-home-manager-files/*)
      original_identity=$(stat -c '%d:%i' -- "$target")
      link_test_checkpoint managed-target-recorded
      if backup_target "$target"; then
        :
      else
        status=$?
        clear_activation_guard "$target"
        return "$status"
      fi
      if [[ $backed_identity != "$original_identity" ]] ||
        [[ ! -L $backed_path ]] || [[ $(readlink -- "$backed_path") != "$current" ]]; then
        if ! restore_recorded_backup "$target"; then
          printf 'Retained changed link in collision journal: %s\n' "$backed_path" >&2
        fi
        clear_activation_guard "$target"
        printf 'Managed link changed before it could be backed up: %s\n' "$target" >&2
        return 1
      fi
      if "$HM_REAL_LN" -Ts -- "$source" "$target"; then
        status=0
        "$HM_REAL_RM" -f -- "$backed_path"
      else
        status=$?
        restore_recorded_backup "$target" || true
      fi
      clear_activation_guard "$target"
      return "$status"
      ;;
    esac
    if backup_target "$target"; then
      :
    else
      status=$?
      clear_activation_guard "$target"
      return "$status"
    fi
  fi
  if [[ -e $target || -L $target ]]; then
    clear_activation_guard "$target"
    printf 'Refusing to overwrite link target that appeared during activation: %s\n' "$target" >&2
    return 1
  fi
  if "$HM_REAL_LN" -Ts -- "$source" "$target"; then
    status=0
  else
    status=$?
  fi
  clear_activation_guard "$target"
  return "$status"
}

if [[ -n $target_directory ]]; then
  for source in "${operands[@]}"; do
    safe_link "$source" "$target_directory/${source##*/}"
  done
elif ((${#operands[@]} == 2)); then
  safe_link "${operands[0]}" "${operands[1]}"
else
  exec "$HM_REAL_LN" "${options[@]}" "${operands[@]}"
fi
