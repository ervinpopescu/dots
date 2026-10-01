#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE="$REPO_ROOT/private_dot_local/private_share/tmux-herdr/tmux-herdr-darwin-helper.c"
INSTALLER_SOURCE="$REPO_ROOT/private_dot_local/private_share/tmux-herdr/tmux-herdr-darwin-installer.c"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CC_BIN="${CC:-cc}"
"$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic -fsyntax-only "$SOURCE"
"$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic "$SOURCE" -o "$TMP_DIR/helper"

selftest="$($TMP_DIR/helper selftest </dev/null)"
[[ "$selftest" == '{"ok":true}' ]]
head -c 16384 /dev/zero | "$TMP_DIR/helper" publish >"$TMP_DIR/exact.out" || true
grep -qx '{"ok":false,"reason":"invalid"}' "$TMP_DIR/exact.out"
head -c 16385 /dev/zero | "$TMP_DIR/helper" publish >"$TMP_DIR/exact-over.out" || true
grep -qx '{"ok":false,"reason":"oversized"}' "$TMP_DIR/exact-over.out"

if "$TMP_DIR/helper" unknown </dev/null >/dev/null 2>&1; then
  echo "helper accepted an unknown action" >&2
  exit 1
fi

oversized="$TMP_DIR/oversized"
python3 - <<'PY' >"$oversized"
print("x" * 70000, end="")
PY
if "$TMP_DIR/helper" publish <"$oversized" >"$TMP_DIR/oversized.out" 2>/dev/null; then
  echo "helper accepted oversized input" >&2
  exit 1
fi
grep -qx '{"ok":false,"reason":"oversized"}' "$TMP_DIR/oversized.out"
if grep -q 'static unsigned counter' "$SOURCE" || ! grep -q 'arc4random_buf' "$SOURCE" || ! grep -q 'attempt < 32U' "$SOURCE" || ! grep -q 'S_ISVTX' "$SOURCE"; then
  echo "helper publication temporary naming is not high-entropy/retry-bounded or lacks sticky intermediate ancestor support" >&2
  exit 1
fi
if ! grep -q '(info.st_uid != owner && info.st_uid != 0)' "$INSTALLER_SOURCE" ||
   grep -q 'install.tmp' "$INSTALLER_SOURCE" ||
   ! grep -q 'arc4random_buf' "$INSTALLER_SOURCE"; then
  echo "native installer lacks trusted ancestors or unique temporary handling" >&2
  exit 1
fi
HOOK_TMPL="$REPO_ROOT/run_onchange_build-tmux-herdr-darwin-helper.sh.tmpl"
if ! grep -q "trap 'rm -rf \"\$BUILD_DIR\"' EXIT" "$HOOK_TMPL" ||
   grep -q '%M' "$HOOK_TMPL" ||
   ! grep -q 'validate_helper_leaf "\$TMP" 1' "$HOOK_TMPL" ||
   ! grep -q 'validate_helper_leaf "\$DEST" 1' "$HOOK_TMPL"; then
  echo "Darwin build hook template contains stat formatting error or lacks trap cleanup" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  "$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic "$SOURCE" -o "$TMP_DIR/helper-darwin"
  "$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic "$INSTALLER_SOURCE" -o "$TMP_DIR/installer-darwin"
  valid='{"v":1,"op":"publish","directory":"/tmp/a b\\\\c\\\"é","publisher_pid":1,"pane_id":"%1","session_kind":"path","session_value":"/tmp/a b\\\\c\\\"é.jsonl"}'
  printf '%s\0' '{"v":1,"op":"publish","directory":"/tmp/x","publisher_pid":1,"pane_id":"%1","session_kind":"id","session_value":"x"}' >"$TMP_DIR/nul-input"
  nul_output="$($TMP_DIR/helper-darwin publish <"$TMP_DIR/nul-input" || true)"
  [[ "$nul_output" == '{"ok":false,"reason":"invalid"}' ]] || {
    echo "Darwin parser accepted embedded NUL input: $nul_output" >&2
    exit 1
  }
  for malformed in \
    "${valid%?},\"unknown\":1}" \
    "{\"v\":1,\"op\":\"publish\",\"v\":1,\"directory\":\"/tmp/x\",\"publisher_pid\":1,\"pane_id\":\"%1\",\"session_kind\":\"id\",\"session_value\":\"x\"}" \
    "{\"v\":1,\"op\":\"publish\",\"directory\":\"/tmp/x\",\"publisher_pid\":999999999999999999999999,\"pane_id\":\"%1\",\"session_kind\":\"id\",\"session_value\":\"x\"}" \
    "${valid} trailing" \
    "{\"v\":1,\"op\":\"publish\",\"directory\":\"/tmp/x\\q\",\"publisher_pid\":1,\"pane_id\":\"%1\",\"session_kind\":\"id\",\"session_value\":\"x\"}"; do
    output="$($TMP_DIR/helper-darwin publish <<<"$malformed" || true)"
    [[ "$output" == '{"ok":false,"reason":"invalid"}' ]] || {
      echo "Darwin parser accepted malformed request: $malformed => $output" >&2
      exit 1
    }
  done
fi
