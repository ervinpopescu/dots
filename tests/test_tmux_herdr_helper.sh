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

# Controlling-terminal verification regression tests
if grep -E 'ttyinfo\.st_rdev == self->tty_dev|self->tty_dev == ttyinfo\.st_rdev' "$SOURCE"; then
  echo "Darwin helper regression: verify_current_tty compares /dev/tty multiplexer st_rdev to self->tty_dev" >&2
  exit 1
fi
if ! grep -q 'NODEV' "$SOURCE" ||
   ! grep -q 'PROC_FLAG_CONTROLT' "$SOURCE" ||
   ! grep -q 'self->pgid != self->tpgid' "$SOURCE" ||
   ! grep -q 'tcgetsid(ttyfd)' "$SOURCE" ||
   ! grep -q 'tcgetpgrp(ttyfd)' "$SOURCE" ||
   ! grep -q 'S_ISCHR(ttyinfo.st_mode)' "$SOURCE"; then
  echo "Darwin helper lacks required controlling-terminal security verification checks" >&2
  exit 1
fi

# Behavioral logic unit test for verify_current_tty
# Note: Linux test execution proves controlling-terminal verification logic and rejection paths;
# it does not claim native Darwin runtime/PTY validation.
cat << 'EOF' > "$TMP_DIR/test_verify_tty.c"
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define PROC_FLAG_CONTROLT 0x40

typedef struct {
  pid_t pid;
  pid_t ppid;
  pid_t pgid;
  pid_t sid;
  dev_t tty_dev;
  pid_t tpgid;
  uint64_t start_sec;
  uint64_t start_usec;
  uint32_t flags;
} process_record;

static int mock_open_ret = 3;
static int mock_fstat_ret = 0;
static mode_t mock_fstat_mode = S_IFCHR | 0620;
static dev_t mock_fstat_rdev = 0x0200; /* /dev/tty multiplexer (e.g. major 2, minor 0) */
static pid_t mock_tcgetsid_ret = 100;
static pid_t mock_tcgetpgrp_ret = 200;

static int mock_open(const char *path, int flags, ...) {
  (void)flags;
  if (strcmp(path, "/dev/tty") != 0) return -1;
  return mock_open_ret;
}

static int mock_fstat(int fd, struct stat *buf) {
  (void)fd;
  if (mock_fstat_ret != 0) return mock_fstat_ret;
  memset(buf, 0, sizeof(*buf));
  buf->st_mode = mock_fstat_mode;
  buf->st_rdev = mock_fstat_rdev;
  return 0;
}

static pid_t mock_tcgetsid(int fd) {
  (void)fd;
  return mock_tcgetsid_ret;
}

static pid_t mock_tcgetpgrp(int fd) {
  (void)fd;
  return mock_tcgetpgrp_ret;
}

static int mock_close(int fd) {
  (void)fd;
  return 0;
}

#define open mock_open
#define fstat mock_fstat
#define tcgetsid mock_tcgetsid
#define tcgetpgrp mock_tcgetpgrp
#define close mock_close

EOF

sed -n '/#ifndef NODEV/,/^}/p' "$SOURCE" >> "$TMP_DIR/test_verify_tty.c"

cat << 'EOF' >> "$TMP_DIR/test_verify_tty.c"
int main(void) {
  process_record self;
  memset(&self, 0, sizeof(self));
  self.pid = 42;
  self.ppid = 1;
  self.pgid = 200;
  self.sid = 100;
  self.tty_dev = 0x1001; /* e_tdev slave PTY device (e.g. ttys001) */
  self.tpgid = 200;
  self.flags = PROC_FLAG_CONTROLT;

  /* 1. Normal case on macOS: multiplexer /dev/tty (0x0200) != slave PTY (0x1001) */
  assert(verify_current_tty(&self) == 0);

  /* 2. Reject NODEV in process metadata */
  self.tty_dev = (dev_t)-1;
  assert(verify_current_tty(&self) == -1);
  self.tty_dev = 0x1001;

  /* 3. Reject missing PROC_FLAG_CONTROLT */
  self.flags = 0;
  assert(verify_current_tty(&self) == -1);
  self.flags = PROC_FLAG_CONTROLT;

  /* 4. Reject background process (pgid != tpgid) */
  self.pgid = 201;
  assert(verify_current_tty(&self) == -1);
  self.pgid = 200;

  /* 5. Reject session mismatch */
  mock_tcgetsid_ret = 101;
  assert(verify_current_tty(&self) == -1);
  mock_tcgetsid_ret = 100;

  /* 6. Reject foreground group mismatch */
  mock_tcgetpgrp_ret = 201;
  assert(verify_current_tty(&self) == -1);
  mock_tcgetpgrp_ret = 200;

  /* 7. Reject non-character device */
  mock_fstat_mode = S_IFREG | 0644;
  assert(verify_current_tty(&self) == -1);
  mock_fstat_mode = S_IFCHR | 0620;

  /* 8. Reject /dev/tty open failure */
  mock_open_ret = -1;
  assert(verify_current_tty(&self) == -1);
  mock_open_ret = 3;

  /* 9. Reject NULL pointer */
  assert(verify_current_tty(NULL) == -1);

  /* 10. Reject non-positive sid / pgid / tpgid */
  self.sid = 0; assert(verify_current_tty(&self) == -1); self.sid = 100;
  self.pgid = 0; assert(verify_current_tty(&self) == -1); self.pgid = 200;
  self.tpgid = 0; assert(verify_current_tty(&self) == -1); self.tpgid = 200;

  return 0;
}
EOF

"$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic "$TMP_DIR/test_verify_tty.c" -o "$TMP_DIR/test_verify_tty"
"$TMP_DIR/test_verify_tty"

# Resolver TTY protocol labels are a fixed, privacy-safe enum.  Exercise every
# categorized rejection and the all-checks-passed path without opening a live
# terminal or inspecting a live process.
for reason in \
  tty_open_failed \
  tty_stat_invalid \
  tty_session_unavailable \
  tty_foreground_unavailable \
  pane_tty_mismatch \
  pane_session_mismatch; do
  if ! grep -q "return \"$reason\"" "$SOURCE"; then
    echo "Darwin resolver is missing fixed TTY reason code: $reason" >&2
    exit 1
  fi
done
cat << 'EOF' > "$TMP_DIR/test_resolve_tty_reason.c"
#include <assert.h>
#include <stddef.h>
#include <string.h>

EOF
sed -n '/static const char \*resolve_tty_failure_reason/,/^}/p' "$SOURCE" >> "$TMP_DIR/test_resolve_tty_reason.c"
cat << 'EOF' >> "$TMP_DIR/test_resolve_tty_reason.c"
int main(void) {
  assert(strcmp(resolve_tty_failure_reason(0, 1, 1, 1, 1, 1), "tty_open_failed") == 0);
  assert(strcmp(resolve_tty_failure_reason(1, 0, 1, 1, 1, 1), "tty_stat_invalid") == 0);
  assert(strcmp(resolve_tty_failure_reason(1, 1, 0, 1, 1, 1), "tty_session_unavailable") == 0);
  assert(strcmp(resolve_tty_failure_reason(1, 1, 1, 0, 1, 1), "tty_foreground_unavailable") == 0);
  assert(strcmp(resolve_tty_failure_reason(1, 1, 1, 1, 0, 1), "pane_tty_mismatch") == 0);
  assert(strcmp(resolve_tty_failure_reason(1, 1, 1, 1, 1, 0), "pane_session_mismatch") == 0);
  assert(resolve_tty_failure_reason(1, 1, 1, 1, 1, 1) == NULL);
  return 0;
}
EOF
"$CC_BIN" -std=c11 -Wall -Wextra -Werror -pedantic "$TMP_DIR/test_resolve_tty_reason.c" -o "$TMP_DIR/test_resolve_tty_reason"
"$TMP_DIR/test_resolve_tty_reason"

HOOK_TMPL="$REPO_ROOT/run_onchange_build-tmux-herdr-darwin-helper.sh.tmpl"
if ! grep -q "trap 'rm -rf \"\$BUILD_DIR\"' EXIT" "$HOOK_TMPL" ||
   grep -q '%M' "$HOOK_TMPL" ||
   ! grep -q 'validate_helper_leaf "\$TMP" 1' "$HOOK_TMPL" ||
   ! grep -q 'validate_helper_leaf "\$DEST" 1' "$HOOK_TMPL" ||
   ! grep -q 'xcrun --sdk macosx --show-sdk-path' "$HOOK_TMPL" ||
   ! grep -q 'errno.h' "$HOOK_TMPL" ||
   ! grep -q '"\$CC" -isysroot "\$SDKROOT" -std=c11 .* "\$SOURCE"' "$HOOK_TMPL" ||
   ! grep -q '"\$CC" -isysroot "\$SDKROOT" -std=c11 .* "\$INSTALLER_SOURCE"' "$HOOK_TMPL"; then
  echo "Darwin build hook template contains stat formatting error, lacks SDK discovery, or omits -isysroot" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  DARWIN_SDKROOT=""
  if command -v xcrun >/dev/null 2>&1; then
    DARWIN_SDKROOT="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)"
  fi
  DARWIN_SYSROOT_FLAGS=()
  if [[ -n "$DARWIN_SDKROOT" && -d "$DARWIN_SDKROOT" ]]; then
    DARWIN_SYSROOT_FLAGS=(-isysroot "$DARWIN_SDKROOT")
  fi
  "$CC_BIN" "${DARWIN_SYSROOT_FLAGS[@]}" -std=c11 -Wall -Wextra -Werror -pedantic "$SOURCE" -o "$TMP_DIR/helper-darwin"
  "$CC_BIN" "${DARWIN_SYSROOT_FLAGS[@]}" -std=c11 -Wall -Wextra -Werror -pedantic "$INSTALLER_SOURCE" -o "$TMP_DIR/installer-darwin"
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
