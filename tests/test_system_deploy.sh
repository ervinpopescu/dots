#!/bin/bash
set -euo pipefail

# Test suite for system-deploy dry-run functionality

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_BIN="$REPO_ROOT/bin/executable_system-deploy.sh"

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

echo "Running system-deploy tests..."

# Test 1: --help option
echo "Test 1: --help displays usage"
help_out="$("$DEPLOY_BIN" --help)"
assert_contains "help contains usage" "Usage: system-deploy.sh [OPTIONS]" "$help_out"
assert_contains "help contains dry-run flag" "-n, --dry-run" "$help_out"

# Test 2: Invalid option exits non-zero
echo "Test 2: Invalid option fails"
if "$DEPLOY_BIN" --invalid-flag >/dev/null 2>&1; then
  echo "  FAIL: invalid flag should return non-zero"
  failures=$((failures + 1))
else
  echo "  PASS: invalid flag returns non-zero"
  passes=$((passes + 1))
fi

# Check if system deployment is supported for this machine profile
check_rendered="$(chezmoi -S "$REPO_ROOT" execute-template '{{ includeTemplate "run_after_system-deploy.sh.tmpl" . }}' 2>/dev/null || true)"
if [ -z "$(echo "$check_rendered" | tr -d '[:space:]')" ]; then
  echo "System deployment is not configured for this machine profile (e.g. non-Linux). Skipping deploy tests."
  echo ""
  echo "Test results: $passes passed, $failures failed"
  exit 0
fi

# Setup isolated test environment for subsequent tests
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

SOURCE_DIR="$TEST_DIR/source"
TARGET_DIR="$TEST_DIR/target"

# Common fixtures: placed under system/etc to be portable across all Linux profiles
mkdir -p "$SOURCE_DIR/system/etc/nginx/conf.d"
mkdir -p "$TARGET_DIR/etc/nginx/conf.d"

# Test 3: Clean state reports no changes
echo "Test 3: Identical files report no changes"
echo "test-clean" > "$SOURCE_DIR/system/etc/nginx/conf.d/clean.conf"
echo "test-clean" > "$TARGET_DIR/etc/nginx/conf.d/clean.conf"

out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" --dry-run)"
assert_contains "clean reports no changes" "No system file changes detected." "$out"

# Test 4: Modified file reports unified diff and zero mutations
echo "Test 4: Modified file unified diff and zero mutations"
echo -e "first line\nsecond line\nthird line" > "$TARGET_DIR/etc/nginx/conf.d/mod.conf"
echo -e "first line\nmodified line\nthird line" > "$SOURCE_DIR/system/etc/nginx/conf.d/mod.conf"

out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" --dry-run)"
assert_contains "shows diff header" "diff --git a/etc/nginx/conf.d/mod.conf b/etc/nginx/conf.d/mod.conf" "$out"
assert_contains "shows removed line" "-second line" "$out"
assert_contains "shows added line" "+modified line" "$out"
assert_contains "reports nginx reload skipped" "[dry-run] Nginx configuration changed; service reload skipped" "$out"
assert_contains "reports count of changed files" "[dry-run] 1 system file(s) would be changed. No system changes applied." "$out"

# Verify target was NOT mutated
target_content="$(cat "$TARGET_DIR/etc/nginx/conf.d/mod.conf")"
assert_contains "target file preserved unchanged" "second line" "$target_content"

# Test 5: New file reports new file mode and full content diff without creating it
echo "Test 5: New file shows diff from /dev/null and is not created"
echo -e "new content line 1\nnew content line 2" > "$SOURCE_DIR/system/etc/nginx/conf.d/new.conf"

out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" -n)"
assert_contains "shows new file header" "diff --git a/etc/nginx/conf.d/new.conf b/etc/nginx/conf.d/new.conf" "$out"
assert_contains "shows new file mode" "new file mode 100644 (root:root)" "$out"
assert_contains "shows dev null diff" "--- /dev/null" "$out"
assert_contains "shows new content in diff" "+new content line 1" "$out"

# Verify target was NOT created
if [ -f "$TARGET_DIR/etc/nginx/conf.d/new.conf" ]; then
  echo "  FAIL: new file should not exist in target after dry run"
  failures=$((failures + 1))
else
  echo "  PASS: new file does not exist in target after dry run"
  passes=$((passes + 1))
fi

# Clean up new.conf from source for next tests
rm -f "$SOURCE_DIR/system/etc/nginx/conf.d/new.conf"

# Test 6: Permissions change diff
echo "Test 6: File mode difference reported without mutating mode"
echo "perm-test" > "$SOURCE_DIR/system/etc/nginx/conf.d/perm.conf"
echo "perm-test" > "$TARGET_DIR/etc/nginx/conf.d/perm.conf"
chmod 600 "$TARGET_DIR/etc/nginx/conf.d/perm.conf"

out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" --dry-run)"
assert_contains "reports mode change" "mode: 600 -> 644" "$out"
assert_contains "notes content unchanged" "(contents unchanged)" "$out"

target_mode="$(stat -c "%a" "$TARGET_DIR/etc/nginx/conf.d/perm.conf")"
assert_eq "target mode remains 600" "600" "$target_mode"

# Test 7: DRY_RUN=1 environment variable activates dry-run
echo "Test 7: DRY_RUN=1 environment variable triggers dry run"
out="$(DRY_RUN=1 SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN")"
assert_contains "env var activates dry run" "No system changes applied." "$out"

# Test 8: SYSTEM_DEPLOY_DRY_RUN=1 environment variable activates dry-run
echo "Test 8: SYSTEM_DEPLOY_DRY_RUN=1 triggers dry run"
out="$(SYSTEM_DEPLOY_DRY_RUN=1 SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN")"
assert_contains "env var activates dry run" "No system changes applied." "$out"

# Test 9: Live deploy applies changes when not in dry run
echo "Test 9: Live deploy writes changes to target"
out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN")"
assert_contains "reports system file changed" "System file changed: /etc/nginx/conf.d/mod.conf" "$out"

target_content_after="$(cat "$TARGET_DIR/etc/nginx/conf.d/mod.conf")"
assert_contains "target file was updated" "modified line" "$target_content_after"

# Test 10: Stale unmanaged files reported (conditioned appropriately by machine profile)
if grep -q "report_stale" <<< "$check_rendered"; then
  echo "Test 10: Stale unmanaged server file warning (server profile)"
  mkdir -p "$SOURCE_DIR/system/hetzner/etc/nginx/conf.d"
  echo "stale content" > "$TARGET_DIR/etc/nginx/conf.d/unmanaged.conf"
  out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" --dry-run)"
  assert_contains "reports stale unmanaged file" "WARN: stale unmanaged server file remains: /etc/nginx/conf.d/unmanaged.conf" "$out"
  rm -f "$TARGET_DIR/etc/nginx/conf.d/unmanaged.conf"
else
  echo "Test 10: Stale workstation server file warning (workstation profile)"
  mkdir -p "$TARGET_DIR/etc/nginx/conf.d"
  echo "stale content" > "$TARGET_DIR/etc/nginx/conf.d/solux.conf"
  out="$(SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" --dry-run)"
  assert_contains "reports stale workstation file" "WARN: stale server file remains on non-hetzner host: /etc/nginx/conf.d/solux.conf" "$out"
  rm -f "$TARGET_DIR/etc/nginx/conf.d/solux.conf"
fi

# Test 11: bin/executable_system-deploy.sh honors SYSTEM_SOURCE_DIR
echo "Test 11: executable_system-deploy.sh honors SYSTEM_SOURCE_DIR"
CUSTOM_SOURCE="$TEST_DIR/custom_source"
mkdir -p "$CUSTOM_SOURCE"
cat << 'EOF' > "$CUSTOM_SOURCE/run_after_system-deploy.sh.tmpl"
{{ if .is_linux -}}
echo "CUSTOM_SOURCE_DEPLOY_RUN"
{{ end -}}
EOF
custom_out="$(SYSTEM_SOURCE_DIR="$CUSTOM_SOURCE" "$DEPLOY_BIN")"
assert_contains "custom SYSTEM_SOURCE_DIR honored" "CUSTOM_SOURCE_DEPLOY_RUN" "$custom_out"

# Test 12: Avoid redundant chmod/chown on unchanged files when metadata is already correct
echo "Test 12: Avoid redundant chmod/chown when metadata is already correct"
chmod 644 "$TARGET_DIR/etc/nginx/conf.d/clean.conf"
ctime_before="$(stat -c "%Z" "$TARGET_DIR/etc/nginx/conf.d/clean.conf")"
sleep 1
SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" >/dev/null
ctime_after="$(stat -c "%Z" "$TARGET_DIR/etc/nginx/conf.d/clean.conf")"
assert_eq "file ctime preserved when metadata already matches" "$ctime_before" "$ctime_after"

# When metadata differs, live deploy updates permissions
chmod 600 "$TARGET_DIR/etc/nginx/conf.d/clean.conf"
SYSTEM_SOURCE_DIR="$SOURCE_DIR" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DEPLOY_BIN" >/dev/null
mode_after="$(stat -c "%a" "$TARGET_DIR/etc/nginx/conf.d/clean.conf")"
assert_eq "file mode updated when metadata differed" "644" "$mode_after"

echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
