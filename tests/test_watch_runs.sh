#!/bin/bash
set -euo pipefail

# Test suite for watch-runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WATCH_RUNS_BIN="$REPO_ROOT/bin/executable_watch-runs"

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

echo "Running watch-runs tests..."

TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

MOCK_REPO="$TEST_DIR/repo"
MOCK_WORKTREE="$TEST_DIR/worktree"
MOCK_BIN="$TEST_DIR/bin"
mkdir -p "$MOCK_REPO" "$MOCK_BIN"

git -C "$MOCK_REPO" init -q -b main
git -C "$MOCK_REPO" config user.name "watch-runs test"
git -C "$MOCK_REPO" config user.email "watch-runs@example.com"
echo "test" > "$MOCK_REPO/README.md"
git -C "$MOCK_REPO" add README.md
git -C "$MOCK_REPO" commit -q -m "test: initialize watch-runs repository"
git -C "$MOCK_REPO" worktree add -q -b feature/watch-runs "$MOCK_WORKTREE"

# Run one watch iteration instead of starting an interactive watcher.
cat > "$MOCK_BIN/watch" <<'EOF'
#!/bin/bash
set -euo pipefail
command="${!#}"
/bin/sh -c "$command"
EOF

# Emulate macOS/BSD column: reject GNU-only -o and pass through accepted output.
cat > "$MOCK_BIN/column" <<'EOF'
#!/bin/bash
set -euo pipefail
for argument in "$@"; do
  if [ "$argument" = "-o" ]; then
    echo "column: illegal option -- o" >&2
    exit 1
  fi
done
cat
EOF

cat > "$MOCK_BIN/no-mistakes" <<'EOF'
#!/bin/bash
if [ "$1" = "axi" ] && [ "$2" = "status" ]; then
  cat <<'STATUS'
  branch: feature/watch-runs
  status: running
  active_steps:
    1,awaiting_approval
STATUS
fi
EOF
chmod +x "$MOCK_BIN/watch" "$MOCK_BIN/column" "$MOCK_BIN/no-mistakes"

echo "Test 1: BSD column accepts watch-runs output"
set +e
watch_output="$(cd "$MOCK_REPO" && PATH="$MOCK_BIN:$PATH" "$WATCH_RUNS_BIN" 2>&1)"
watch_status=$?
set -e
assert_eq "watch-runs succeeds with BSD column behavior" "0" "$watch_status"
assert_contains "reports active run" "feature/watch-runs running 1 (AWAITING APPROVAL)" "$watch_output"
assert_not_contains "does not use GNU column -o" "illegal option -- o" "$watch_output"

echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
