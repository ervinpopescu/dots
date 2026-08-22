#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: hm-switch PROFILE [HOME_MANAGER_OPTION...]

Examples:
  hm-switch ervin@lenovo
  hm-switch ervin@cloudtop --impure

Set HM_FLAKE to use a flake path other than the current directory.
USAGE
  exit 2
}

[[ $# -ge 1 ]] || usage
profile=$1
shift

case "$profile" in
*[!A-Za-z0-9@._-]* | "")
  echo "invalid Home Manager profile: $profile" >&2
  exit 1
  ;;
esac

: "${HOME_MANAGER_BIN:?HOME_MANAGER_BIN must be set by the Nix wrapper}"
: "${HM_BACKUP_COMMAND:?HM_BACKUP_COMMAND must be set by the Nix wrapper}"
: "${HM_RESTORE_COMMAND:?HM_RESTORE_COMMAND must be set by the Nix wrapper}"
: "${HOME:?HOME must be set}"

current_generation() {
  local candidate
  for candidate in \
    "${XDG_STATE_HOME:-$HOME/.local/state}/home-manager/gcroots/current-home" \
    "$HOME/.local/share/home-manager/gcroots/current-home"; do
    if [[ -e $candidate ]]; then
      readlink -e -- "$candidate"
      return
    fi
  done
}

flake=${HM_FLAKE:-.}
state_root=${XDG_STATE_HOME:-"$HOME/.local/state"}/home-manager/collision-backups

umask 077
mkdir -p -- "$state_root"
session=$(mktemp -d "$state_root/hm-before-nix-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
backup_id=${session##*/}
: >"$session/manifest"
printf 'pending\n' >"$session/status"
printf 'profile=%s\nflake=%s\ncreated=%s\n' \
  "$profile" "$flake" "$(date -u +%FT%TZ)" >"$session/metadata"

export HM_BACKUP_ID=$backup_id
export HM_BACKUP_SESSION=$session

restore_mode=--forward
for option in "$@"; do
  if [[ $option == --rollback ]]; then
    restore_mode=--rollback
  fi
done

hm_options=()
case "$profile" in
*@cloudtop)
  hm_options+=(--impure)
  ;;
esac
hm_options+=("$@")
old_generation=$(current_generation || true)

if "$HOME_MANAGER_BIN" -B "$HM_BACKUP_COMMAND" switch \
  "${hm_options[@]}" --flake "$flake#$profile"; then
  new_generation=$(current_generation || true)
  if [[ -n $new_generation ]]; then
    "$HM_RESTORE_COMMAND" "$restore_mode" "$old_generation" "$new_generation" "$new_generation"
  fi
  if [[ -s "$session/manifest" ]]; then
    printf 'active\n' >"$session/status"
    ln -sfn -- "$backup_id" "$state_root/latest"
    printf 'Backup manifest: %s\n' "$session/manifest"
  else
    rm -rf -- "$session"
    printf 'No unmanaged collisions required backup.\n'
  fi
else
  printf 'failed\n' >"$session/status"
  echo "Home Manager activation failed; retained manifest: $session/manifest" >&2
  exit 1
fi
