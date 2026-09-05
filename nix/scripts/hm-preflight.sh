#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: hm-preflight PROFILE [--content] [--yes] [NIX_BUILD_OPTION...]

Shows path-level additions, changes, collisions, and removals without activation.
--content prints unified text diffs and may reveal local secrets; it requires an
interactive confirmation unless --yes is also supplied.

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

show_content=0
assume_yes=0
nix_options=()
for option in "$@"; do
  case "$option" in
  --content) show_content=1 ;;
  --yes) assume_yes=1 ;;
  *) nix_options+=("$option") ;;
  esac
done

if ((show_content && !assume_yes)); then
  if [[ ! -t 0 ]]; then
    echo "--content requires an interactive terminal or --yes" >&2
    exit 1
  fi
  printf 'Content diffs may print secrets from existing files. Continue? [y/N] '
  read -r confirmation
  case "$confirmation" in
  y | Y | yes | YES) ;;
  *)
    echo "Cancelled."
    exit 1
    ;;
  esac
fi

: "${NIX_BIN:?NIX_BIN must be set by the Nix wrapper}"
: "${HM_STORE_DIR:?HM_STORE_DIR must be set by the Nix wrapper}"
: "${HOME:?HOME must be set}"
flake=${HM_FLAKE:-.}
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
generation="$work/generation"
attribute="$flake#homeConfigurations.\"$profile\".activationPackage"

build_options=(build "$attribute" --out-link "$generation")
case "$profile" in
*@cloudtop) build_options+=(--impure) ;;
esac
build_options+=("${nix_options[@]}")
"$NIX_BIN" "${build_options[@]}"

new_files="$generation/home-files"
if [[ ! -d "$new_files" ]]; then
  echo "activation package has no home-files tree: $generation" >&2
  exit 1
fi

print_content_diff() {
  local status=$1 target=$2 generated=$3
  ((show_content)) || return 0

  case "$status" in
  ADD)
    if [[ -f "$generated" ]] &&
      { grep -Iq . "$generated" || [[ ! -s "$generated" ]]; }; then
      diff -u --label /dev/null --label "generated:$target" /dev/null "$generated" || true
    else
      echo "Binary or non-file content omitted: $target"
    fi
    ;;
  CHANGE | COLLISION)
    if [[ -f "$target" && -f "$generated" ]] &&
      { grep -Iq . "$target" || [[ ! -s "$target" ]]; } &&
      { grep -Iq . "$generated" || [[ ! -s "$generated" ]]; }; then
      diff -u --label "current:$target" --label "generated:$target" "$target" "$generated" || true
    else
      echo "Binary or non-file content omitted: $target"
    fi
    ;;
  esac
}

change_count=0
while IFS= read -r -d '' generated; do
  relative=${generated#"$new_files"/}
  target="$HOME/$relative"
  status=

  if [[ ! -e "$target" && ! -L "$target" ]]; then
    status=ADD
  elif [[ -L "$target" ]]; then
    current_source=$(readlink -- "$target")
    if [[ $current_source == "$generated" ]]; then
      continue
    fi
    case "$current_source" in
    "$HM_STORE_DIR"/*-home-manager-files/*) status=CHANGE ;;
    *) status=COLLISION ;;
    esac
  else
    status=COLLISION
  fi

  printf '%-9s %s\n' "$status" "$target"
  print_content_diff "$status" "$target" "$generated"
  ((change_count += 1))
done < <(find -H "$new_files" \( -type f -o -type l \) -print0 | sort -z)

case "$profile" in
*@lenovo | *@cloudtop | *@hp)
  runtime_settings="$HOME/.config/VSCodium/User/settings.json"
  if [[ ! -e "$runtime_settings" && ! -L "$runtime_settings" ]]; then
    printf '%-9s %s\n' INITIALIZE "$runtime_settings"
    ((change_count += 1))
  fi
  ;;
esac

state_home=${XDG_STATE_HOME:-"$HOME/.local/state"}
current_profile=
if [[ -e "$state_home/nix/profiles/home-manager" ]]; then
  current_profile="$state_home/nix/profiles/home-manager"
elif [[ -e "/nix/var/nix/profiles/per-user/$USER/home-manager" ]]; then
  current_profile="/nix/var/nix/profiles/per-user/$USER/home-manager"
fi

if [[ -n "$current_profile" && -d "$current_profile/home-files" ]]; then
  current_files="$current_profile/home-files"
  while IFS= read -r -d '' current; do
    relative=${current#"$current_files"/}
    if [[ ! -e "$new_files/$relative" && ! -L "$new_files/$relative" ]]; then
      target="$HOME/$relative"
      printf '%-9s %s\n' REMOVE "$target"
      if ((show_content)) && [[ -f "$current" ]] &&
        { grep -Iq . "$current" || [[ ! -s "$current" ]]; }; then
        diff -u --label "current-generation:$target" --label /dev/null "$current" /dev/null || true
      fi
      ((change_count += 1))
    fi
  done < <(find -H "$current_files" \( -type f -o -type l \) -print0 | sort -z)
fi

printf '\n%d managed path change(s); no files were activated.\n' "$change_count"
if ((!show_content)); then
  echo "Run again with --content to request unified text diffs."
fi
