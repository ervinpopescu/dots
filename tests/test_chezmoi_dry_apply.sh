#!/bin/bash
set -euo pipefail

# Test suite for chezmoi-dry-apply helper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DRY_APPLY_BIN="$REPO_ROOT/bin/executable_chezmoi-dry-apply"

passes=0
failures=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  PASS: $label"
    passes=$((passes + 1))
  else
    echo "  FAIL: $label"
    echo "    Expected: '$expected'"
    echo "    Actual:   '$actual'"
    failures=$((failures + 1))
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  PASS: $label"
    passes=$((passes + 1))
  else
    echo "  FAIL: $label (did not find '$needle' in output)"
    echo "    Output was: $haystack"
    failures=$((failures + 1))
  fi
}

echo "Running chezmoi-dry-apply tests..."

# Test 1: --help displays usage
echo "Test 1: --help displays usage"
help_out="$("$DRY_APPLY_BIN" --help)"
assert_contains "help contains usage" "Usage: chezmoi-dry-apply [OPTIONS]" "$help_out"
assert_contains "help mentions chezmoi apply dry-run" "chezmoi apply --dry-run --verbose" "$help_out"
assert_contains "help mentions system-deploy dry-run" "system-deploy.sh --dry-run" "$help_out"

# Test 2: Error on missing argument to -S
echo "Test 2: Missing argument to -S fails"
if "$DRY_APPLY_BIN" -S >/dev/null 2>&1; then
  echo "  FAIL: -S without path should return non-zero"
  failures=$((failures + 1))
else
  echo "  PASS: -S without path returns non-zero"
  passes=$((passes + 1))
fi

# Setup isolated test environment
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

ISOLATED_SOURCE="$TEST_DIR/source"
ISOLATED_DEST="$TEST_DIR/dest"
ISOLATED_SYS_TARGET="$TEST_DIR/sys_target"

mkdir -p "$ISOLATED_SOURCE" "$ISOLATED_DEST" "$ISOLATED_SYS_TARGET/etc/nginx/conf.d"

profile_is_macbook="$(chezmoi -S "$REPO_ROOT" execute-template '{{ .is_macbook }}')"
rendered_helper_hook="$(chezmoi -S "$REPO_ROOT" execute-template --override-data '{"is_macbook":true}' -f run_onchange_build-tmux-herdr-darwin-helper.sh.tmpl)"
assert_contains "Darwin hook validates parents before writes" "validate_parent" "$rendered_helper_hook"
assert_contains "Darwin hook rejects symlinks" '[[ -e "$DEST_DIR" || -L "$DEST_DIR" ]]' "$rendered_helper_hook"
assert_contains "Darwin hook validates destination leaf" "validate_helper_leaf \"\$DEST\"" "$rendered_helper_hook"
assert_contains "Darwin hook discovers SDK path" 'xcrun --sdk macosx --show-sdk-path' "$rendered_helper_hook"
assert_contains "Darwin hook verifies standard headers" 'usr/include/errno.h' "$rendered_helper_hook"
assert_contains "Darwin hook compiles helper with explicit isysroot" '"$CC" -isysroot "$SDKROOT"' "$rendered_helper_hook"
assert_contains "Darwin hook compiles installer with explicit isysroot" '"$CC" -isysroot "$SDKROOT" -std=c11 -Wall -Wextra -Werror -O2 "$INSTALLER_SOURCE"' "$rendered_helper_hook"
if [[ "$rendered_helper_hook" == *".tmux-herdr-darwin-helper.build.lock"* ]]; then
  echo "  FAIL: Darwin hook retains a permanent fixed lock"
  failures=$((failures + 1))
else
  echo "  PASS: Darwin hook has no permanent fixed lock"
  passes=$((passes + 1))
fi

# Behavioral test for Darwin hook SDK resolution and failure when absent
sdk_test_dir="$TEST_DIR/sdk_test"
mock_home="$sdk_test_dir/home"
mock_bin="$sdk_test_dir/bin"
mkdir -p "$mock_home/.local/share/tmux-herdr" "$mock_home/.local/libexec" "$mock_bin"
chmod 700 "$mock_home" "$mock_home/.local" "$mock_home/.local/share" "$mock_home/.local/share/tmux-herdr" "$mock_home/.local/libexec"
cp "$REPO_ROOT/private_dot_local/private_share/tmux-herdr/tmux-herdr-darwin-helper.c" "$mock_home/.local/share/tmux-herdr/"
cp "$REPO_ROOT/private_dot_local/private_share/tmux-herdr/tmux-herdr-darwin-installer.c" "$mock_home/.local/share/tmux-herdr/"
chmod 600 "$mock_home/.local/share/tmux-herdr/"*

cat << 'EOF' > "$mock_bin/stat"
#!/bin/bash
fmt=""
target=""
while [ $# -gt 0 ]; do
  if [ "$1" = "-f" ]; then
    fmt="$2"
    shift 2
  else
    target="$1"
    shift
  fi
done

if [ "$fmt" = "%HT" ]; then
  if [ -d "$target" ]; then echo "Directory"; else echo "Regular File"; fi
elif [ "$fmt" = "%u" ]; then
  id -u
elif [ "$fmt" = "%Lp" ]; then
  /usr/bin/stat -c "%a" "$target" 2>/dev/null || echo "700"
else
  /usr/bin/stat "$@"
fi
EOF
chmod 700 "$mock_bin/stat"

cat << 'EOF' > "$mock_bin/xcrun"
#!/bin/bash
if [[ "$*" == *"--find clang"* ]]; then
  echo "$(dirname "$0")/clang"
  exit 0
fi
exit 1
EOF
chmod 700 "$mock_bin/xcrun"

cat << 'EOF' > "$mock_bin/clang"
#!/bin/bash
exit 0
EOF
chmod 700 "$mock_bin/clang"

hook_script="$sdk_test_dir/run_hook.sh"
echo "$rendered_helper_hook" > "$hook_script"
chmod 700 "$hook_script"

set +e
missing_sdk_err="$(HOME="$mock_home" PATH="$mock_bin:/usr/bin:/bin" bash "$hook_script" 2>&1)"
missing_sdk_status=$?
set -e

if [ $missing_sdk_status -ne 0 ] && [[ "$missing_sdk_err" == *"active macOS SDK or standard headers"* ]]; then
  echo "  PASS: Darwin hook fails closed when macOS SDK is absent"
  passes=$((passes + 1))
else
  echo "  FAIL: Darwin hook did not fail closed on missing SDK (status=$missing_sdk_status output=$missing_sdk_err)"
  failures=$((failures + 1))
fi

mock_sdk="$sdk_test_dir/MacOSX.sdk"
mkdir -p "$mock_sdk/usr/include"
touch "$mock_sdk/usr/include/errno.h" "$mock_sdk/usr/include/libproc.h"

cat << EOF > "$mock_bin/xcrun"
#!/bin/bash
if [[ "\$*" == *"--find clang"* ]]; then
  echo "\$(dirname "\$0")/clang"
  exit 0
fi
if [[ "\$*" == *"--show-sdk-path"* ]]; then
  echo "$mock_sdk"
  exit 0
fi
exit 1
EOF
chmod 700 "$mock_bin/xcrun"

compiler_log="$sdk_test_dir/compiler.log"
cat << EOF > "$mock_bin/clang"
#!/bin/bash
echo "CLANG_ARGS: \$*" >> "$compiler_log"
prev=""
for arg in "\$@"; do
  if [ "\$prev" = "-o" ]; then
    out="\$arg"
    cat << "OUT_EOF" > "\$out"
#!/bin/bash
if [ "\$1" = "selftest" ]; then
  exit 0
fi
if [ -n "\$2" ]; then
  cp "\$1" "\$2/tmux-herdr-darwin-helper"
  chmod 700 "\$2/tmux-herdr-darwin-helper"
fi
exit 0
OUT_EOF
    chmod 700 "\$out"
  fi
  prev="\$arg"
done
exit 0
EOF
chmod 700 "$mock_bin/clang"

set +e
sdk_success_out="$(HOME="$mock_home" PATH="$mock_bin:/usr/bin:/bin" bash "$hook_script" 2>&1)"
sdk_success_status=$?
set -e

if [ $sdk_success_status -eq 0 ] && grep -q -- "-isysroot $mock_sdk" "$compiler_log"; then
  echo "  PASS: Darwin hook invokes compiler with explicit -isysroot SDKROOT"
  passes=$((passes + 1))
else
  echo "  FAIL: Darwin hook failed to supply -isysroot (status=$sdk_success_status output=$sdk_success_out)"
  failures=$((failures + 1))
fi

compile_count="$(grep -c -- "-isysroot $mock_sdk" "$compiler_log" || true)"
if [ "$compile_count" -eq 2 ]; then
  echo "  PASS: Both helper and installer were compiled with explicit -isysroot"
  passes=$((passes + 1))
else
  echo "  FAIL: Expected 2 compilations with -isysroot, got $compile_count"
  failures=$((failures + 1))
fi
if [ "$profile_is_macbook" = "true" ]; then
  echo "Test: macOS XDG environment renders tool configuration"
  macos_vars="$(chezmoi -S "$REPO_ROOT" execute-template '{{ includeTemplate "dot_config/zsh/env/vars.zsh.tmpl" . }}')"
  assert_contains "Docker uses XDG config" "export DOCKER_CONFIG=\"\$XDG_CONFIG_HOME\"/docker" "$macos_vars"
  assert_contains "Vim uses XDG config" 'export VIMINIT=' "$macos_vars"

  system_source_file="$ISOLATED_SOURCE/system/macos/etc/zshenv"
  system_target_file="$ISOLATED_SYS_TARGET/etc/zshenv"
  system_diff_header="diff --git a/etc/zshenv b/etc/zshenv"
else
  system_source_file="$ISOLATED_SOURCE/system/etc/nginx/conf.d/test.conf"
  system_target_file="$ISOLATED_SYS_TARGET/etc/nginx/conf.d/test.conf"
  system_diff_header="diff --git a/etc/nginx/conf.d/test.conf b/etc/nginx/conf.d/test.conf"
fi

# Configure minimal chezmoi source with both a user dotfile and system deploy template
cat << 'EOF' > "$ISOLATED_SOURCE/.chezmoiignore"
system/**
tests/**
EOF

# User dotfile managed by chezmoi
mkdir -p "$ISOLATED_SOURCE/dot_config/testapp"
mkdir -p "$ISOLATED_DEST/.config/testapp"
echo "original-dotfile" > "$ISOLATED_DEST/.config/testapp/config.txt"
echo "modified-dotfile" > "$ISOLATED_SOURCE/dot_config/testapp/config.txt"

# System file managed by system/ tree
mkdir -p "$(dirname "$system_source_file")" "$(dirname "$system_target_file")"
echo "original-sys" > "$system_target_file"
echo "modified-sys" > "$system_source_file"

# Copy system-deploy template into isolated source
cp "$REPO_ROOT/run_after_system-deploy.sh.tmpl" "$ISOLATED_SOURCE/run_after_system-deploy.sh.tmpl"
mkdir -p "$ISOLATED_SOURCE/bin"
cp "$REPO_ROOT/bin/executable_system-deploy.sh" "$ISOLATED_SOURCE/bin/executable_system-deploy.sh"
chmod +x "$ISOLATED_SOURCE/bin/executable_system-deploy.sh"

# Test 3: chezmoi-dry-apply previews BOTH user dotfiles and system deploy
echo "Test 3: Previews both user dotfiles and system changes without mutating either"
out="$(SYSTEM_TARGET_DIR="$ISOLATED_SYS_TARGET" "$DRY_APPLY_BIN" -S "$ISOLATED_SOURCE" -D "$ISOLATED_DEST")"

assert_contains "shows dotfile diff header" "diff --git a/.config/testapp/config.txt b/.config/testapp/config.txt" "$out"
assert_contains "shows dotfile diff addition" "+modified-dotfile" "$out"
assert_contains "shows system diff header" "$system_diff_header" "$out"
assert_contains "shows system diff addition" "+modified-sys" "$out"
assert_contains "shows system dry-run summary" "[dry-run] 1 system file(s) would be changed. No system changes applied." "$out"

# Verify neither user target nor system target was modified
dest_content="$(cat "$ISOLATED_DEST/.config/testapp/config.txt")"
assert_eq "user target not modified" "original-dotfile" "$dest_content"

sys_content="$(cat "$system_target_file")"
assert_eq "system target not modified" "original-sys" "$sys_content"

# Test 4: When clean, system deploy reports no changes
echo "Test 4: Clean state reports no changes"
echo "modified-dotfile" > "$ISOLATED_DEST/.config/testapp/config.txt"
echo "modified-sys" > "$system_target_file"

clean_out="$(SYSTEM_TARGET_DIR="$ISOLATED_SYS_TARGET" "$DRY_APPLY_BIN" -S "$ISOLATED_SOURCE" -D "$ISOLATED_DEST")"
assert_contains "reports no system file changes" "No system file changes detected." "$clean_out"

# Test 5: Target argument forwarding
echo "Test 5: Target arguments restrict dotfile preview"
echo "unrelated-change" > "$ISOLATED_SOURCE/dot_config/testapp/config.txt"
mkdir -p "$ISOLATED_SOURCE/dot_config/otherapp" "$ISOLATED_DEST/.config/otherapp"
echo "other-original" > "$ISOLATED_DEST/.config/otherapp/other.txt"
echo "other-modified" > "$ISOLATED_SOURCE/dot_config/otherapp/other.txt"

target_out="$(SYSTEM_TARGET_DIR="$ISOLATED_SYS_TARGET" "$DRY_APPLY_BIN" -S "$ISOLATED_SOURCE" -D "$ISOLATED_DEST" "$ISOLATED_DEST/.config/otherapp/other.txt")"
assert_contains "shows specified target diff" ".config/otherapp/other.txt" "$target_out"

# Test 6: SYSTEM_DEPLOY_BIN override honored
echo "Test 6: SYSTEM_DEPLOY_BIN override honored"
MOCK_DEPLOY="$TEST_DIR/mock_deploy.sh"
cat << 'EOF' > "$MOCK_DEPLOY"
#!/bin/bash
echo "MOCK_DEPLOY_CALLED: $*"
EOF
chmod +x "$MOCK_DEPLOY"

mock_out="$(SYSTEM_DEPLOY_BIN="$MOCK_DEPLOY" "$DRY_APPLY_BIN" -S "$ISOLATED_SOURCE" -D "$ISOLATED_DEST")"
assert_contains "mock deploy was called with --dry-run" "MOCK_DEPLOY_CALLED: --dry-run" "$mock_out"

# Test 7: Failure propagation from chezmoi apply
echo "Test 7: Failure from invalid chezmoi argument returns non-zero"
if "$DRY_APPLY_BIN" --invalid-argument-xyz >/dev/null 2>&1; then
  echo "  FAIL: invalid chezmoi argument should return non-zero"
  failures=$((failures + 1))
else
  echo "  PASS: invalid chezmoi argument returns non-zero"
  passes=$((passes + 1))
fi

echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
