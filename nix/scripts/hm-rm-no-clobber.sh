#!/usr/bin/env bash
set -euo pipefail

: "${HM_BACKUP_COMMAND:?HM_BACKUP_COMMAND must be set by the Nix wrapper}"
: "${HM_REAL_RM:?HM_REAL_RM must be set by the Nix wrapper}"
: "${HM_RENAME_NOREPLACE_BIN:?HM_RENAME_NOREPLACE_BIN must be set by the Nix wrapper}"
: "${HM_STORE_DIR:?HM_STORE_DIR must be set by the Nix wrapper}"
: "${HOME:?HOME must be set}"

HM_STORE_DIR=$(readlink -f -- "$HM_STORE_DIR")

force=0
recursive=0
operands=()
for argument in "$@"; do
  case "$argument" in
  --force | -f) force=1 ;;
  --recursive | -r | -R) recursive=1 ;;
  --verbose | -v | --) ;;
  -*) exec "$HM_REAL_RM" "$@" ;;
  *) operands+=("$argument") ;;
  esac
done

if ((force || recursive || ${#operands[@]} != 1)); then
  exec "$HM_REAL_RM" "$@"
fi

target=${operands[0]}
case "$target" in
"$HOME"/*) ;;
*) exec "$HM_REAL_RM" "$@" ;;
esac

expected_identity=$(stat -c '%d:%i' -- "$target")
expected_source=
if [[ -L $target ]]; then
  expected_source=$(readlink -- "$target")
fi

checkpoint=${HM_REMOVE_TEST_CHECKPOINT_DIR:-}
if [[ -n $checkpoint ]]; then
  : >"$checkpoint/remove-target-observed.ready"
  while [[ ! -e $checkpoint/remove-target-observed.continue ]]; do
    sleep 0.01
  done
fi

result=$(mktemp)
if HM_BACKUP_RESULT_FILE="$result" "$HM_BACKUP_COMMAND" "$target"; then
  status=0
else
  status=$?
fi
if ((status != 0)); then
  "$HM_REAL_RM" -f -- "$result"
  exit "$status"
fi
mapfile -d '' -t fields <"$result"
"$HM_REAL_RM" -f -- "$result"
if ((${#fields[@]} != 3)); then
  echo "backup command did not return a complete transaction result" >&2
  exit 1
fi
held=${fields[1]}
held_identity=${fields[2]}

if [[ $held_identity == "$expected_identity" ]] &&
  [[ -L $held ]] && [[ $(readlink -- "$held") == "$expected_source" ]]; then
  case "$expected_source" in
  "$HM_STORE_DIR"/*-home-manager-files/*)
    "$HM_REAL_RM" -- "$held"
    exit 0
    ;;
  esac
fi

if "$HM_RENAME_NOREPLACE_BIN" "$held" "$target"; then
  printf 'Refusing to remove path that replaced a managed link: %s\n' "$target" >&2
else
  printf 'Retained changed path in collision journal: %s\n' "$held" >&2
fi
exit 1
