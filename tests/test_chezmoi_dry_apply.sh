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
mkdir -p "$ISOLATED_SOURCE/system/etc/nginx/conf.d"
echo "original-sys" > "$ISOLATED_SYS_TARGET/etc/nginx/conf.d/test.conf"
echo "modified-sys" > "$ISOLATED_SOURCE/system/etc/nginx/conf.d/test.conf"

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
assert_contains "shows system diff header" "diff --git a/etc/nginx/conf.d/test.conf b/etc/nginx/conf.d/test.conf" "$out"
assert_contains "shows system diff addition" "+modified-sys" "$out"
assert_contains "shows system dry-run summary" "[dry-run] 1 system file(s) would be changed. No system changes applied." "$out"

# Verify neither user target nor system target was modified
dest_content="$(cat "$ISOLATED_DEST/.config/testapp/config.txt")"
assert_eq "user target not modified" "original-dotfile" "$dest_content"

sys_content="$(cat "$ISOLATED_SYS_TARGET/etc/nginx/conf.d/test.conf")"
assert_eq "system target not modified" "original-sys" "$sys_content"

# Test 4: When clean, system deploy reports no changes
echo "Test 4: Clean state reports no changes"
echo "modified-dotfile" > "$ISOLATED_DEST/.config/testapp/config.txt"
echo "modified-sys" > "$ISOLATED_SYS_TARGET/etc/nginx/conf.d/test.conf"

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
