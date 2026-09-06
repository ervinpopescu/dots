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

assert_not_contains() {
  local label="$1" needle="$2" haystack="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    echo "  PASS: $label"
    passes=$((passes + 1))
  else
    echo "  FAIL: $label (unexpectedly found '$needle' in output)"
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
trap 'chmod -R 777 "$TEST_DIR" 2>/dev/null || true; rm -rf "$TEST_DIR"' EXIT

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

# Test 13: Tracked Transmission source is preserved and not decommissioned
if grep -q "report_stale" <<< "$check_rendered"; then
  echo "Test 13: Tracked transmission source is preserved and not treated as decommissioned"
  TRACKED_SRC="$TEST_DIR/tracked_trans_src"
  TRACKED_TGT="$TEST_DIR/tracked_trans_tgt"
  mkdir -p "$TRACKED_SRC/system/hetzner/etc/nginx/conf.d"
  mkdir -p "$TRACKED_SRC/system/hetzner/etc/systemd/system/transmission.service.d"
  echo "server { listen 9091; }" > "$TRACKED_SRC/system/hetzner/etc/nginx/conf.d/transmission.conf"
  echo "[Service]" > "$TRACKED_SRC/system/hetzner/etc/systemd/system/transmission.service.d/override.conf"

  mkdir -p "$TRACKED_TGT/etc/nginx/conf.d"
  mkdir -p "$TRACKED_TGT/etc/systemd/system/transmission.service.d"
  echo "old nginx config" > "$TRACKED_TGT/etc/nginx/conf.d/transmission.conf"
  echo "old service dropin" > "$TRACKED_TGT/etc/systemd/system/transmission.service.d/override.conf"

  # Dry-run: shows diff, does not report decommissioned
  out_tracked_dry="$(SYSTEM_SOURCE_DIR="$TRACKED_SRC" SYSTEM_TARGET_DIR="$TRACKED_TGT" "$DEPLOY_BIN" --dry-run)"
  assert_contains "diff shown for tracked transmission config" "diff --git a/etc/nginx/conf.d/transmission.conf b/etc/nginx/conf.d/transmission.conf" "$out_tracked_dry"
  assert_not_contains "tracked nginx config not previewed as decommissioned" "[dry-run] would remove decommissioned transmission config: /etc/nginx/conf.d/transmission.conf" "$out_tracked_dry"
  assert_not_contains "tracked dropin not previewed as decommissioned" "[dry-run] would remove decommissioned transmission config: /etc/systemd/system/transmission.service.d" "$out_tracked_dry"

  # Live mode: updates target and does not remove
  out_tracked_live="$(SYSTEM_SOURCE_DIR="$TRACKED_SRC" SYSTEM_TARGET_DIR="$TRACKED_TGT" "$DEPLOY_BIN")"
  assert_contains "reports transmission config changed" "System file changed: /etc/nginx/conf.d/transmission.conf" "$out_tracked_live"
  assert_not_contains "tracked nginx config not removed as decommissioned" "Removing decommissioned transmission config: /etc/nginx/conf.d/transmission.conf" "$out_tracked_live"
  assert_not_contains "tracked dropin not removed as decommissioned" "Removing decommissioned transmission config: /etc/systemd/system/transmission.service.d" "$out_tracked_live"
  if [ -f "$TRACKED_TGT/etc/nginx/conf.d/transmission.conf" ] && [ -f "$TRACKED_TGT/etc/systemd/system/transmission.service.d/override.conf" ]; then
    echo "  PASS: tracked transmission configs exist in target after live deploy"
    passes=$((passes + 1))
  else
    echo "  FAIL: tracked transmission configs missing after live deploy"
    failures=$((failures + 1))
  fi
  tracked_content="$(cat "$TRACKED_TGT/etc/nginx/conf.d/transmission.conf")"
  assert_contains "target was updated to tracked source content" "server { listen 9091; }" "$tracked_content"
fi

# Test 14: Genuine decommissioned target is reported in dry run and removed in live mode
if grep -q "report_stale" <<< "$check_rendered"; then
  echo "Test 14: Genuine decommissioned target reported in dry-run and removed in live mode"
  DECOM_SRC="$TEST_DIR/decom_src"
  DECOM_TGT="$TEST_DIR/decom_tgt"
  mkdir -p "$DECOM_SRC/system/hetzner" # No transmission configs in source
  mkdir -p "$DECOM_TGT/etc/nginx/conf.d"
  mkdir -p "$DECOM_TGT/etc/systemd/system/transmission-daemon.service.d"
  echo "stale nginx" > "$DECOM_TGT/etc/nginx/conf.d/transmission.conf"
  echo "stale daemon dropin" > "$DECOM_TGT/etc/systemd/system/transmission-daemon.service.d/override.conf"

  # Dry-run
  out_decom_dry="$(SYSTEM_SOURCE_DIR="$DECOM_SRC" SYSTEM_TARGET_DIR="$DECOM_TGT" "$DEPLOY_BIN" --dry-run)"
  assert_contains "previews transmission nginx removal" "[dry-run] would remove decommissioned transmission config: /etc/nginx/conf.d/transmission.conf" "$out_decom_dry"
  assert_contains "previews transmission daemon dropin removal" "[dry-run] would remove decommissioned transmission config: /etc/systemd/system/transmission-daemon.service.d" "$out_decom_dry"
  assert_contains "reports nginx reload skipped" "[dry-run] Nginx configuration changed; service reload skipped" "$out_decom_dry"

  # Target files must NOT be deleted in dry-run
  if [ -f "$DECOM_TGT/etc/nginx/conf.d/transmission.conf" ] && [ -f "$DECOM_TGT/etc/systemd/system/transmission-daemon.service.d/override.conf" ]; then
    echo "  PASS: transmission configs preserved during dry run"
    passes=$((passes + 1))
  else
    echo "  FAIL: transmission configs were deleted during dry run"
    failures=$((failures + 1))
  fi

  # Live mode: files are deleted
  out_decom_live="$(SYSTEM_SOURCE_DIR="$DECOM_SRC" SYSTEM_TARGET_DIR="$DECOM_TGT" "$DEPLOY_BIN")"
  assert_contains "reports live removal of nginx config" "Removing decommissioned transmission config: /etc/nginx/conf.d/transmission.conf" "$out_decom_live"
  assert_contains "reports live removal of daemon dropin" "Removing decommissioned transmission config: /etc/systemd/system/transmission-daemon.service.d" "$out_decom_live"
  if [ ! -e "$DECOM_TGT/etc/nginx/conf.d/transmission.conf" ] && [ ! -e "$DECOM_TGT/etc/systemd/system/transmission-daemon.service.d" ]; then
    echo "  PASS: transmission configs removed during live deploy"
    passes=$((passes + 1))
  else
    echo "  FAIL: transmission configs were not removed during live deploy"
    failures=$((failures + 1))
  fi
fi

# Test 15: Non-writable DEST_ROOT cannot cause deletion of host /etc or call sudo
if grep -q "report_stale" <<< "$check_rendered"; then
  echo "Test 15: Non-writable DEST_ROOT cannot escape to host /etc or call sudo"
  RO_TGT="$TEST_DIR/ro_tgt"
  mkdir -p "$RO_TGT/etc/systemd/system/transmission-daemon.service.d"
  echo "stale daemon dropin" > "$RO_TGT/etc/systemd/system/transmission-daemon.service.d/override.conf"
  # Make directory non-writable so rm -rf fails inside target
  chmod 555 "$RO_TGT/etc/systemd/system"

  SUDO_LOG="$TEST_DIR/sudo_invocations.log"
  MOCK_BIN_RO="$TEST_DIR/mock_bin_ro"
  mkdir -p "$MOCK_BIN_RO"
  cat << EOF > "$MOCK_BIN_RO/sudo"
#!/bin/bash
echo "SUDO_CALLED: \$*" >> "$SUDO_LOG"
exit 1
EOF
  chmod +x "$MOCK_BIN_RO/sudo"

  set +e
  ro_out="$(PATH="$MOCK_BIN_RO:$PATH" SYSTEM_SOURCE_DIR="$DECOM_SRC" SYSTEM_TARGET_DIR="$RO_TGT" "$DEPLOY_BIN" 2>&1)"
  set -euo pipefail

  chmod 755 "$RO_TGT/etc/systemd/system"

  if [ -f "$SUDO_LOG" ]; then
    echo "  FAIL: sudo was called during execution with non-writable DEST_ROOT: $(cat "$SUDO_LOG")"
    failures=$((failures + 1))
  else
    echo "  PASS: sudo was never called when DEST_ROOT was non-writable"
    passes=$((passes + 1))
  fi
  assert_not_contains "host /etc never referenced in destructive command" "rm -rf /etc" "$ro_out"
fi

# Setup mock environment for worktree and protocol tests
MOCK_BIN="$TEST_DIR/mock_bin"
mkdir -p "$MOCK_BIN"
LEGACY_SOURCE="$TEST_DIR/legacy_source"
mkdir -p "$LEGACY_SOURCE/system/etc/nginx/conf.d"
cat << 'EOF' > "$LEGACY_SOURCE/run_after_system-deploy.sh.tmpl"
{{ if .is_linux -}}
#!/bin/bash
set -euo pipefail
echo "LEGACY_EXECUTED"
{{ end -}}
EOF

REAL_CHEZMOI="$(command -v chezmoi)"
cat << EOF > "$MOCK_BIN/chezmoi"
#!/bin/bash
if [ "\$1" = "source-path" ]; then
  echo "$LEGACY_SOURCE"
  exit 0
fi
exec "$REAL_CHEZMOI" "\$@"
EOF
chmod +x "$MOCK_BIN/chezmoi"

INSTALLED_BIN="$TEST_DIR/installed_bin"
mkdir -p "$INSTALLED_BIN"
cp "$DEPLOY_BIN" "$INSTALLED_BIN/system-deploy.sh"
chmod +x "$INSTALLED_BIN/system-deploy.sh"

FEATURE_WT="$TEST_DIR/feature_wt"
mkdir -p "$FEATURE_WT/system/etc/nginx/conf.d"
git -C "$FEATURE_WT" init -q
cp "$REPO_ROOT/run_after_system-deploy.sh.tmpl" "$FEATURE_WT/run_after_system-deploy.sh.tmpl"
echo "feature-wt-content" > "$FEATURE_WT/system/etc/nginx/conf.d/feat-wt.conf"

# Test 16: Installed wrapper called inside a feature worktree resolves that worktree's source
echo "Test 16: Installed wrapper inside worktree resolves worktree source instead of chezmoi source-path"
wt_out="$(
  cd "$FEATURE_WT"
  PATH="$MOCK_BIN:$PATH" SYSTEM_TARGET_DIR="$TARGET_DIR" "$INSTALLED_BIN/system-deploy.sh" --dry-run
)"
assert_contains "worktree source diff shown" "feat-wt.conf" "$wt_out"
assert_contains "dry-run summary shown" "No system changes applied." "$wt_out"
assert_not_contains "legacy source template was not executed" "LEGACY_EXECUTED" "$wt_out"

# Test 17: Dry-run fails closed on unsupported legacy template
echo "Test 17: Dry-run fails closed on unsupported legacy template"
OUTSIDE_DIR="$TEST_DIR/outside_wt"
mkdir -p "$OUTSIDE_DIR"
set +e
legacy_out="$(
  cd "$OUTSIDE_DIR"
  PATH="$MOCK_BIN:$PATH" SYSTEM_TARGET_DIR="$TARGET_DIR" "$INSTALLED_BIN/system-deploy.sh" --dry-run 2>&1
)"
legacy_status=$?
set -euo pipefail

if [ "$legacy_status" -ne 0 ]; then
  echo "  PASS: dry-run exits non-zero on legacy template"
  passes=$((passes + 1))
else
  echo "  FAIL: dry-run exited zero on legacy template"
  failures=$((failures + 1))
fi
assert_contains "clear protocol error displayed" "Error: system deployment template does not support dry-run protocol." "$legacy_out"
assert_contains "abort warning displayed" "Aborting to prevent unintentional live system modifications." "$legacy_out"
assert_not_contains "legacy template was not executed" "LEGACY_EXECUTED" "$legacy_out"

# Test 18: Combined wrapper (chezmoi-dry-apply) passes selected worktree source to both sides
echo "Test 18: chezmoi-dry-apply passes worktree source to chezmoi apply and system deployment"
CHEZMOI_LOG="$TEST_DIR/chezmoi_calls.log"
cat << EOF > "$MOCK_BIN/chezmoi"
#!/bin/bash
if [ "\$1" = "source-path" ]; then
  echo "$LEGACY_SOURCE"
  exit 0
fi
if [[ " \$* " == *" apply "* ]]; then
  echo "CHEZMOI_APPLY_ARGS: \$*" >> "$CHEZMOI_LOG"
  exit 0
fi
exec "$REAL_CHEZMOI" "\$@"
EOF
chmod +x "$MOCK_BIN/chezmoi"

DRY_APPLY_BIN="$REPO_ROOT/bin/executable_chezmoi-dry-apply"
dry_apply_out="$(
  cd "$FEATURE_WT"
  PATH="$MOCK_BIN:$PATH" SYSTEM_TARGET_DIR="$TARGET_DIR" "$DRY_APPLY_BIN"
)"
chezmoi_log_content="$(cat "$CHEZMOI_LOG")"
assert_contains "chezmoi apply received worktree source" "-S $FEATURE_WT apply --dry-run" "$chezmoi_log_content"
assert_contains "system deploy previewed worktree file" "feat-wt.conf" "$dry_apply_out"

echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
