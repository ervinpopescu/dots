#!/usr/bin/env bash
set -euo pipefail

: "${DARWIN_REBUILD_BIN:?DARWIN_REBUILD_BIN must be set by the Nix wrapper}"
: "${HM_RESTORE_COMMAND:?HM_RESTORE_COMMAND must be set by the Nix wrapper}"
: "${NIX_STORE_BIN:?NIX_STORE_BIN must be set by the Nix wrapper}"
: "${SUDO_BIN:?SUDO_BIN must be set by the Nix wrapper}"

restore_mode=--forward
for option in "$@"; do
  if [[ $option == --rollback ]]; then
    restore_mode=--rollback
  fi
done

current_system=${DARWIN_CURRENT_SYSTEM:-/run/current-system}
managed_state=${XDG_STATE_HOME:-"$HOME/.local/state"}/home-manager/collision-backups/active-managed-generation
old_managed_state_identity=
if [[ -f $managed_state ]]; then
  old_managed_state_identity=$(stat -c '%d:%i' -- "$managed_state")
fi
old_generation=$(readlink -e "$current_system" 2>/dev/null || true)
"$SUDO_BIN" "$DARWIN_REBUILD_BIN" switch "$@"
new_generation=$(readlink -e "$current_system" 2>/dev/null || true)

if [[ -n $new_generation ]]; then
  managed_generation=
  if [[ -f $managed_state ]] &&
    [[ $(stat -c '%d:%i' -- "$managed_state") != "$old_managed_state_identity" ]]; then
    IFS= read -r -d '' managed_generation <"$managed_state" || true
  fi
  if [[ $restore_mode == --rollback && -z $managed_generation ]]; then
    candidate_count=0
    while IFS= read -r candidate; do
      if [[ -d $candidate/home-files && -x $candidate/activate && -f $candidate/hm-version ]]; then
        managed_generation=$candidate
        ((candidate_count += 1))
      fi
    done < <("$NIX_STORE_BIN" --query --requisites "$new_generation")
    if ((candidate_count != 1)); then
      managed_generation=
    fi
  fi
  "$HM_RESTORE_COMMAND" "$restore_mode" "$old_generation" "$new_generation" "$managed_generation"
fi
