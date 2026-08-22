#!/usr/bin/env bash
set -euo pipefail

: "${HOME:?HOME must be set}"

if (($# < 1)); then
  echo "usage: hm-check-collisions NEW_GENERATION_FILES [SOURCE...]" >&2
  exit 2
fi

new_files=$1
shift
collision_count=0

for source in "$@"; do
  relative=${source#"$new_files"/}
  target="$HOME/$relative"

  if [[ -L "$target" ]]; then
    continue
  fi
  if [[ ! -e "$target" ]]; then
    continue
  fi
  if cmp -s -- "$source" "$target"; then
    continue
  fi
  if [[ -n ${HOME_MANAGER_BACKUP_COMMAND:-} ]]; then
    continue
  fi

  printf 'Existing path would be clobbered: %s\n' "$target" >&2
  ((collision_count += 1))
done

if ((collision_count > 0)); then
  echo "Run activation through hm-switch so collisions are backed up." >&2
  exit 1
fi
