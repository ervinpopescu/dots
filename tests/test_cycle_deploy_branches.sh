#!/bin/bash
set -euo pipefail

# ==============================================================================
# Test suite for cycle-deploy-branches
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CYCLE_BIN="$REPO_ROOT/bin/executable_cycle-deploy-branches"

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
    echo "  FAIL: $label (found unexpected '$needle' in output)"
    failures=$((failures + 1))
  fi
}

echo "Running cycle-deploy-branches tests..."

# ------------------------------------------------------------------------------
# Test 1: --help displays usage
# ------------------------------------------------------------------------------
echo "Test 1: --help displays usage"
help_out="$("$CYCLE_BIN" --help)"
assert_contains "help contains usage" "cycle-deploy-branches [OPTIONS]" "$help_out"
assert_contains "help contains --status" "--status" "$help_out"
assert_contains "help contains --dry-run" "--dry-run" "$help_out"
assert_contains "help contains --only-failed" "--only-failed" "$help_out"
assert_contains "help contains --skip-passed" "--skip-passed" "$help_out"
assert_contains "help contains example config" ".cycle-deploy.json" "$help_out"

# ------------------------------------------------------------------------------
# Test 2: Error when outside a git repository
# ------------------------------------------------------------------------------
echo "Test 2: Error outside git repository"
nongit_dir="$(mktemp -d)"
pushd "$nongit_dir" >/dev/null
set +e
nongit_out="$("$CYCLE_BIN" 2>&1)"
nongit_status=$?
set -e
popd >/dev/null
rm -rf "$nongit_dir"
assert_eq "exit code non-zero outside git" "1" "$nongit_status"
assert_contains "error message mentions git repository" "Not inside a git repository" "$nongit_out"

# ------------------------------------------------------------------------------
# Setup Mock Git Repository with Worktrees
# ------------------------------------------------------------------------------
echo "Setting up mock repository and worktrees..."
MOCK_ROOT="$(mktemp -d)"
trap 'rm -rf "$MOCK_ROOT"' EXIT

MOCK_REPO="$MOCK_ROOT/repo"
mkdir -p "$MOCK_REPO"
cd "$MOCK_REPO"
git init -b main >/dev/null 2>&1 || (git init >/dev/null 2>&1 && git checkout -b main >/dev/null 2>&1)
git config user.name "Cycle Test"
git config user.email "test@example.com"
echo "Initial content" > README.md
echo "SECRET=12345" > .env
mkdir -p terraform
echo "terraform config" > terraform/main.tf
git add README.md .env terraform/main.tf
git commit -m "chore: initial commit" >/dev/null

# Create 3 feature worktrees
WT_DIR="$MOCK_ROOT/worktrees"
mkdir -p "$WT_DIR"
git worktree add "$WT_DIR/feat1" -b feature/one >/dev/null 2>&1
git worktree add "$WT_DIR/feat2" -b feature/two >/dev/null 2>&1
git worktree add "$WT_DIR/feat3" -b feature/three >/dev/null 2>&1

# Add commits in worktrees
echo "feature 1 work" >> "$WT_DIR/feat1/README.md"
git -C "$WT_DIR/feat1" commit -am "feat: feature one" >/dev/null

echo "feature 2 work" >> "$WT_DIR/feat2/README.md"
git -C "$WT_DIR/feat2" commit -am "feat: feature two" >/dev/null

echo "feature 3 work" >> "$WT_DIR/feat3/README.md"
git -C "$WT_DIR/feat3" commit -am "feat: feature three" >/dev/null

# ------------------------------------------------------------------------------
# Test 3: Missing .cycle-deploy.json gives clear error and template
# ------------------------------------------------------------------------------
echo "Test 3: Missing config error"
cd "$MOCK_REPO"
set +e
no_cfg_out="$("$CYCLE_BIN" 2>&1)"
no_cfg_status=$?
set -e
assert_eq "missing config exits with 1" "1" "$no_cfg_status"
assert_contains "mentions no cycle-deploy configuration" "No cycle-deploy configuration found" "$no_cfg_out"
assert_contains "shows example config" "Example .cycle-deploy.json" "$no_cfg_out"

# ------------------------------------------------------------------------------
# Test 4: --state-file and --json
# ------------------------------------------------------------------------------
echo "Test 4: --state-file and --json"
state_file_out="$("$CYCLE_BIN" --state-file)"
assert_eq "state file path is inside .git" "$MOCK_REPO/.git/cycle-deploy-state.json" "$state_file_out"

json_out="$("$CYCLE_BIN" --json)"
assert_contains "json contains repo name" '"repo": "repo"' "$json_out"

# ------------------------------------------------------------------------------
# Test 5: Create .cycle-deploy.json and test --dry-run
# ------------------------------------------------------------------------------
echo "Test 5: Create .cycle-deploy.json and test --dry-run"
cat > "$MOCK_REPO/.cycle-deploy.json" << 'EOF'
{
  "name": "mock-app",
  "env": {
    "APP_ENV": "${ENV:-testing}",
    "TEST_FLAG": "true"
  },
  "sync": [
    ".env",
    "terraform/"
  ],
  "steps": [
    {
      "name": "Mock Lint",
      "command": "echo 'running lint'"
    },
    {
      "name": "Mock Test",
      "command": "echo 'running test'"
    }
  ],
  "manual_test": {
    "enabled": true,
    "info": [
      "Target env: $APP_ENV"
    ],
    "instructions": [
      "1. Verify mock test output"
    ]
  }
}
EOF

dry_out="$("$CYCLE_BIN" --dry-run)"
assert_contains "dry-run preview header" "[DRY-RUN PREVIEW]" "$dry_out"
assert_contains "dry-run shows env var" "APP_ENV" "$dry_out"
assert_contains "dry-run shows sync" ".env -> .env" "$dry_out"
assert_contains "dry-run shows steps" "Mock Lint" "$dry_out"
assert_contains "dry-run shows instructions" "Verify mock test output" "$dry_out"
assert_contains "dry-run completed" "Dry-run completed for feature/one" "$dry_out"

# Ensure state file was NOT created during dry run
if [ -f "$state_file_out" ]; then
  echo "  FAIL: dry-run created state file"
  failures=$((failures + 1))
else
  echo "  PASS: dry-run did not create state file"
  passes=$((passes + 1))
fi

# ------------------------------------------------------------------------------
# Test 6: --status with initial worktrees shows PENDING
# ------------------------------------------------------------------------------
echo "Test 6: --status shows PENDING worktrees"
status_out="$("$CYCLE_BIN" --status)"
assert_contains "status table has header" "DEPLOYMENT STATUS OVERVIEW" "$status_out"
assert_contains "feature/one is pending" "feature/one" "$status_out"
assert_contains "feature/two is pending" "feature/two" "$status_out"
assert_contains "feature/three is pending" "feature/three" "$status_out"
assert_contains "pending count is 3" "Pending: 3" "$status_out"

# ------------------------------------------------------------------------------
# Test 7: Deployment with simulated inputs (Pass, Skip, Fail)
# ------------------------------------------------------------------------------
echo "Test 7: Deployment recording (Pass on feat1)"
# feature/one: 'y' to deploy, Enter to confirm manual test
printf "y\n\n" | "$CYCLE_BIN" --branch feature/one >/dev/null 2>&1

b1_state="$("$CYCLE_BIN" --json)"
assert_contains "feature/one recorded as passed" '"status": "passed"' "$b1_state"

# Verify .env was synced to worktree
if [ -f "$WT_DIR/feat1/.env" ] && grep -q "SECRET=12345" "$WT_DIR/feat1/.env"; then
  echo "  PASS: .env was synced to worktree"
  passes=$((passes + 1))
else
  echo "  FAIL: .env was not synced to worktree"
  failures=$((failures + 1))
fi

echo "Test 7b: Deployment recording (Skip on feat2)"
# feature/two: 'n' to skip
printf "n\n" | "$CYCLE_BIN" --branch feature/two >/dev/null 2>&1
b2_state="$("$CYCLE_BIN" --json)"
assert_contains "feature/two recorded as skipped" '"status": "skipped"' "$b2_state"

echo "Test 7c: Deployment recording (Fail on feat3)"
# Configure failing step for feature/three
cat > "$WT_DIR/feat3/.cycle-deploy.json" << 'EOF'
{
  "name": "mock-app",
  "steps": [
    {
      "name": "Failing Step",
      "command": "exit 42"
    }
  ],
  "manual_test": {
    "enabled": false
  }
}
EOF
# feature/three: 'y' to start, then 's' to skip failed step
printf "y\ns\n" | "$CYCLE_BIN" --branch feature/three >/dev/null 2>&1
b3_state="$("$CYCLE_BIN" --json)"
assert_contains "feature/three recorded as failed" '"status": "failed"' "$b3_state"
assert_contains "feature/three recorded failed_step" '"failed_step": "Failing Step"' "$b3_state"
assert_contains "feature/three recorded exit code 42" '"exit_code": 42' "$b3_state"

# ------------------------------------------------------------------------------
# Test 8: --status reflects updated states
# ------------------------------------------------------------------------------
echo "Test 8: --status shows updated states"
updated_status="$("$CYCLE_BIN" --status)"
assert_contains "feature/one shows PASSED" "PASSED" "$updated_status"
assert_contains "feature/two shows SKIPPED" "SKIPPED" "$updated_status"
assert_contains "feature/three shows FAILED" "FAILED" "$updated_status"
assert_contains "summary counts passed" "Passed: 1" "$updated_status"
assert_contains "summary counts failed" "Failed: 1" "$updated_status"
assert_contains "summary counts skipped" "Skipped: 1" "$updated_status"

# ------------------------------------------------------------------------------
# Test 9: --skip-passed auto-skips passed branch
# ------------------------------------------------------------------------------
echo "Test 9: --skip-passed"
skip_out="$("$CYCLE_BIN" --skip-passed --branch feature/one)"
assert_contains "auto-skips passed branch" "Auto-skipping branch 'feature/one'" "$skip_out"

# ------------------------------------------------------------------------------
# Test 10: --only-failed filters to only failed/skipped/unrecorded
# ------------------------------------------------------------------------------
echo "Test 10: --only-failed"
only_failed_dry="$("$CYCLE_BIN" --only-failed --dry-run)"
assert_not_contains "feature/one excluded from only-failed" "Dry-run completed for feature/one" "$only_failed_dry"
assert_contains "feature/two included in only-failed" "Dry-run completed for feature/two" "$only_failed_dry"
assert_contains "feature/three included in only-failed" "Dry-run completed for feature/three" "$only_failed_dry"

# ------------------------------------------------------------------------------
# Test 11: --clear-state resets state
# ------------------------------------------------------------------------------
echo "Test 11: --clear-state"
clear_out="$("$CYCLE_BIN" --clear-state)"
assert_contains "clear state confirms" "Cleared deployment state file" "$clear_out"

cleared_status="$("$CYCLE_BIN" --status)"
assert_contains "all branches back to pending" "Pending: 3" "$cleared_status"
assert_contains "passed is 0" "Passed: 0" "$cleared_status"

# ------------------------------------------------------------------------------
# Test 12: Branch testing plan extraction (PR_MESSAGE.md, TESTING.md, fallback)
# ------------------------------------------------------------------------------
echo "Test 12: Branch testing plan extraction"

# 12a. Create PR_MESSAGE.md in feature/one
cat > "$WT_DIR/feat1/PR_MESSAGE.md" << 'EOF'
# feat(one): implement something

### Summary
Did work.

### Testing Plan
1. Automated: run pytest
2. Manual: check browser alert

### Next Steps
Deploy to prod.
EOF

# 12b. Create standalone TESTING.md in feature/two
cat > "$WT_DIR/feat2/TESTING.md" << 'EOF'
Custom test steps:
- Verify staging DB connection
- Test API endpoint response
EOF

# feature/three has no test plan file
rm -f "$WT_DIR/feat3/.cycle-deploy.json"

# Update .cycle-deploy.json with test_plan
cat > "$MOCK_REPO/.cycle-deploy.json" << 'EOF'
{
  "name": "mock-app",
  "test_plan": {
    "files": ["PR_MESSAGE.md", "TESTING.md", "TEST_PLAN.md"],
    "section": "Testing Plan"
  },
  "steps": [
    { "name": "Lint", "command": "true" }
  ],
  "manual_test": {
    "enabled": true,
    "instructions": ["Generic test instruction"]
  }
}
EOF

# Test dry-run on feature/one (extracts PR_MESSAGE.md section)
tp1_out="$("$CYCLE_BIN" --dry-run --branch feature/one)"
assert_contains "feat1 extracts test plan header" "Branch Testing Plan (from PR_MESSAGE.md)" "$tp1_out"
assert_contains "feat1 extracts automated item" "1. Automated: run pytest" "$tp1_out"
assert_contains "feat1 extracts manual item" "2. Manual: check browser alert" "$tp1_out"
assert_not_contains "feat1 stops before next section" "Deploy to prod" "$tp1_out"

# Test dry-run on feature/two (extracts full TESTING.md)
tp2_out="$("$CYCLE_BIN" --dry-run --branch feature/two)"
assert_contains "feat2 extracts test plan from TESTING.md" "Branch Testing Plan (from TESTING.md)" "$tp2_out"
assert_contains "feat2 contains custom test step" "Verify staging DB connection" "$tp2_out"

# Test dry-run on feature/three (falls back cleanly)
tp3_out="$("$CYCLE_BIN" --dry-run --branch feature/three)"
assert_contains "feat3 shows fallback message" "(No branch-specific test plan found in worktree)" "$tp3_out"
assert_contains "feat3 shows generic instructions" "Generic test instruction" "$tp3_out"

# Test status table detail indicator
status_tp_out="$("$CYCLE_BIN" --status)"
assert_contains "status table shows plan indicator for feat1" "plan: PR_MESSAGE.md" "$status_tp_out"
assert_contains "status table shows plan indicator for feat2" "plan: TESTING.md" "$status_tp_out"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "Test Results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
exit 0
