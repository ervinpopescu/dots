#!/bin/bash
set -euo pipefail

# Test suite for wt-nm repository resolution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WT_NM_BIN="$REPO_ROOT/bin/executable_wt-nm"

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

echo "Running wt-nm tests..."

TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

MOCK_BIN="$TEST_DIR/bin"
REPO_DIR="$TEST_DIR/repo with spaces"
NON_GIT_DIR="$TEST_DIR/not-a-repository"
mkdir -p "$MOCK_BIN" "$REPO_DIR/subdirectory" "$NON_GIT_DIR"
EXPECTED_REPO_DIR="$(cd "$REPO_DIR" && pwd -P)"
git -C "$REPO_DIR" init -q

cat > "$MOCK_BIN/clear" <<'EOF'
#!/bin/bash
exit 0
EOF

cat > "$MOCK_BIN/no-mistakes" <<'EOF'
#!/bin/bash
printf '%s\n' "$PWD" > "$NM_CALLS"
EOF

cat > "$MOCK_BIN/wt" <<'EOF'
#!/bin/bash
count=0
if [ -f "$WT_CALLS" ]; then
  count=$(cat "$WT_CALLS")
fi
count=$((count + 1))
printf '%s\n' "$count" > "$WT_CALLS"
if [ "$count" -eq 1 ]; then
  printf '%s\n' "$PWD"
fi
EOF

cat > "$MOCK_BIN/find" <<'EOF'
#!/bin/bash
if [ -n "${FZF_FIND_REPO:-}" ]; then
  printf '%s/.git\n' "$FZF_FIND_REPO"
fi
EOF

cat > "$MOCK_BIN/fzf" <<'EOF'
#!/bin/bash
: > "$FZF_CALLED_FILE"
cat
EOF

chmod +x "$MOCK_BIN"/*

run_wt_nm() {
  local cwd="$1"
  shift
  (
    cd "$cwd"
    PATH="$MOCK_BIN:$PATH" \
      WT_CALLS="$TEST_DIR/wt.calls" \
      NM_CALLS="$TEST_DIR/nm.calls" \
      FZF_FIND_REPO="${FZF_FIND_REPO:-}" \
      FZF_CALLED_FILE="$TEST_DIR/fzf.called" \
      "$WT_NM_BIN" "$@"
  )
}

reset_mocks() {
  rm -f "$TEST_DIR/wt.calls" "$TEST_DIR/nm.calls" "$TEST_DIR/fzf.called"
  FZF_FIND_REPO=""
}

echo "Test 1: Explicit absolute path resolves repository without fzf"
reset_mocks
output="$(run_wt_nm "$TEST_DIR" "$REPO_DIR/")"
assert_not_contains "absolute path does not launch fzf" "Searching for git repositories..." "$output"
assert_eq "absolute path runs no-mistakes in repository" "$EXPECTED_REPO_DIR" "$(cat "$TEST_DIR/nm.calls")"
[ ! -e "$TEST_DIR/fzf.called" ]


echo "Test 2: Explicit relative path with spaces resolves repository"
reset_mocks
output="$(run_wt_nm "$TEST_DIR" "repo with spaces/subdirectory")"
assert_not_contains "relative path does not launch fzf" "Searching for git repositories..." "$output"
assert_eq "relative path resolves repository root" "$EXPECTED_REPO_DIR" "$(cat "$TEST_DIR/nm.calls")"


echo "Test 3: No argument uses current Git repository without fzf"
reset_mocks
output="$(run_wt_nm "$REPO_DIR")"
assert_not_contains "current repository does not launch fzf" "Searching for git repositories..." "$output"
assert_eq "current repository runs no-mistakes" "$EXPECTED_REPO_DIR" "$(cat "$TEST_DIR/nm.calls")"


echo "Test 4: No argument falls back to fzf outside a Git repository"
reset_mocks
FZF_FIND_REPO="$REPO_DIR"
output="$(run_wt_nm "$NON_GIT_DIR")"
assert_contains "fallback announces repository search" "Searching for git repositories..." "$output"
assert_eq "fallback runs no-mistakes in selected repository" "$REPO_DIR" "$(cat "$TEST_DIR/nm.calls")"
[ -e "$TEST_DIR/fzf.called" ]


echo "Test 5: Nonexistent explicit path fails clearly"
reset_mocks
if output="$(run_wt_nm "$TEST_DIR" "$TEST_DIR/missing" 2>&1)"; then
  status=0
else
  status=$?
fi
assert_eq "nonexistent path returns failure" "1" "$status"
assert_contains "nonexistent path reports the path" "Selected repository directory does not exist: $TEST_DIR/missing" "$output"


echo "Test 6: Non-Git explicit path fails clearly"
reset_mocks
if output="$(run_wt_nm "$TEST_DIR" "$NON_GIT_DIR" 2>&1)"; then
  status=0
else
  status=$?
fi
assert_eq "non-Git path returns failure" "1" "$status"
assert_contains "non-Git path reports the problem" "Selected directory is not a git repository: $NON_GIT_DIR" "$output"


echo "Test 7: More than one argument shows usage"
reset_mocks
if output="$(run_wt_nm "$TEST_DIR" "$REPO_DIR" extra 2>&1)"; then
  status=0
else
  status=$?
fi
assert_eq "extra argument returns usage failure" "2" "$status"
assert_contains "extra argument reports usage" "Usage: wt-nm [REPOSITORY]" "$output"


echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
