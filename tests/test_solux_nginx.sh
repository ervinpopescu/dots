#!/bin/bash
set -euo pipefail

# ==============================================================================
# Isolated test suite for Solux Nginx configuration
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

passes=0
failures=0

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

echo "Running Solux Nginx configuration tests..."

# Check that nginx binary exists
if ! command -v nginx >/dev/null 2>&1; then
  echo "nginx binary not found in PATH; skipping isolated Nginx runtime tests."
  exit 0
fi

TEST_DIR="$(mktemp -d)"
PORT=19473
CONF_FILE="$TEST_DIR/nginx.conf"
PID_FILE="$TEST_DIR/nginx.pid"
LOG_DIR="$TEST_DIR/logs"
WWW_DIR="$TEST_DIR/www"
SNIPPETS_DIR="$TEST_DIR/snippets"

cleanup() {
  if [ -f "$PID_FILE" ]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
  fi
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

mkdir -p "$LOG_DIR" "$WWW_DIR/solux/assets" "$SNIPPETS_DIR"

# Copy the actual snippet from the repository
cp "$REPO_ROOT/system/hetzner/etc/nginx/snippets/solux-security-headers.conf" "$SNIPPETS_DIR/solux-security-headers.conf"

# Create fixture files representing Vite PWA build outputs
echo "<!doctype html><title>Solux</title>" >"$WWW_DIR/solux/index.html"
echo "console.log('sw');" >"$WWW_DIR/solux/sw.js"
echo "console.log('registerSW');" >"$WWW_DIR/solux/registerSW.js"
echo '{"name":"Solux"}' >"$WWW_DIR/solux/manifest.webmanifest"
echo "console.log('workbox');" >"$WWW_DIR/solux/workbox-9c191d2f.js"
# Ensure hashed JS bundle exceeds gzip_min_length (256 bytes) to verify compression
{
  echo "console.log('hashed-js');"
  for i in {1..20}; do
    echo "// Solux solar calculation engine asset payload padding $i"
  done
} >"$WWW_DIR/solux/assets/index-Vew5OthO.js"
echo "body { color: black; }" >"$WWW_DIR/solux/assets/index-CaUFehCr.css"
echo "icon-data" >"$WWW_DIR/solux/favicon.ico"

# Read solux.conf from repository and substitute the snippet include path for testing
SOLUX_CONF_CONTENT="$(cat "$REPO_ROOT/system/hetzner/etc/nginx/conf.d/solux.conf")"
ADAPTED_SOLUX_CONF="${SOLUX_CONF_CONTENT//\/etc\/nginx\/snippets\/solux-security-headers.conf/$SNIPPETS_DIR\/solux-security-headers.conf}"

# Generate isolated nginx configuration
cat <<EOF >"$CONF_FILE"
pid $PID_FILE;
error_log $LOG_DIR/error.log;
events {
    worker_connections 64;
}
http {
    access_log $LOG_DIR/access.log;
    include /etc/nginx/mime.types;

    server {
        listen 127.0.0.1:$PORT;

        # Inject repository-managed Solux configuration adapted to test root
        $ADAPTED_SOLUX_CONF
    }
}
EOF

# Substitute root /var/www with test www dir
sed -i "s|root /var/www;|root $WWW_DIR;|g" "$CONF_FILE"

# Test 1: Syntax check with nginx -t
echo "Test 1: Isolated Nginx syntax test"
syntax_out="$(nginx -t -c "$CONF_FILE" 2>&1)"
assert_contains "syntax is ok" "syntax is ok" "$syntax_out"
assert_contains "test is successful" "test is successful" "$syntax_out"

# Start isolated Nginx server for behavior validation
nginx -c "$CONF_FILE"
# Wait briefly for worker readiness
sleep 0.5

# Test 2: Exact redirect /solux -> /solux/
echo "Test 2: Exact redirect /solux -> /solux/"
redirect_headers="$(curl -sI "http://127.0.0.1:$PORT/solux")"
assert_contains "returns 301 Moved Permanently" "HTTP/1.1 301 Moved Permanently" "$redirect_headers"
assert_contains "redirects to /solux/" "Location: http://127.0.0.1:$PORT/solux/" "$redirect_headers"

# Test 3: Root fallback /solux/ returns index.html with no-store/revalidate
echo "Test 3: Root /solux/ returns index with lifecycle no-store headers"
root_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/")"
assert_contains "returns 200 OK" "HTTP/1.1 200 OK" "$root_headers"
assert_contains "cache control is no-store" "Cache-Control: no-store, no-cache, must-revalidate" "$root_headers"
assert_contains "HSTS header present" "Strict-Transport-Security: max-age=31536000; includeSubDomains" "$root_headers"
assert_contains "X-Content-Type-Options present" "X-Content-Type-Options: nosniff" "$root_headers"
assert_contains "X-Frame-Options DENY present" "X-Frame-Options: DENY" "$root_headers"
assert_contains "Permissions-Policy contains geolocation" "Permissions-Policy: geolocation=(self)" "$root_headers"
assert_contains "CSP contains OpenFreeMap" "https://tiles.openfreemap.org" "$root_headers"
assert_contains "CSP contains Nominatim" "https://nominatim.openstreetmap.org" "$root_headers"
assert_contains "CSP contains Overpass" "https://overpass-api.de" "$root_headers"
assert_contains "CSP contains worker-src blob:" "worker-src 'self' blob:" "$root_headers"

# Test 4: SPA client route fallback (/solux/map) returns index.html
echo "Test 4: SPA subroute fallback /solux/map"
spa_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/map")"
assert_contains "returns 200 OK" "HTTP/1.1 200 OK" "$spa_headers"
assert_contains "cache control is no-store for SPA fallback" "Cache-Control: no-store, no-cache, must-revalidate" "$spa_headers"

# Test 5: Lifecycle files (sw.js, registerSW.js, manifest.webmanifest, workbox-*.js) have no-store
echo "Test 5: Lifecycle files have no-store cache headers"
for lifecycle_file in sw.js registerSW.js manifest.webmanifest workbox-9c191d2f.js; do
  lf_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/$lifecycle_file")"
  assert_contains "$lifecycle_file returns 200" "HTTP/1.1 200 OK" "$lf_headers"
  assert_contains "$lifecycle_file has no-store" "Cache-Control: no-store, no-cache, must-revalidate" "$lf_headers"
  assert_contains "$lifecycle_file retains CSP" "Content-Security-Policy:" "$lf_headers"
done

# Test 6: Hashed assets (/solux/assets/*) have immutable cache headers
echo "Test 6: Hashed assets have immutable cache headers"
for asset in index-Vew5OthO.js index-CaUFehCr.css; do
  asset_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/assets/$asset")"
  assert_contains "$asset returns 200" "HTTP/1.1 200 OK" "$asset_headers"
  assert_contains "$asset has immutable cache" "Cache-Control: public, max-age=31536000, immutable" "$asset_headers"
  assert_contains "$asset retains CSP" "Content-Security-Policy:" "$asset_headers"
done

# Test 7: Missing asset returns 404 and does NOT fall back to index.html
echo "Test 7: Missing asset returns 404"
missing_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/assets/missing-chunk-xyz.js")"
assert_contains "missing asset returns 404" "HTTP/1.1 404 Not Found" "$missing_headers"
if [[ "$missing_headers" == *"immutable"* ]]; then
  echo "  FAIL: missing asset 404 response should not be marked immutable"
  failures=$((failures + 1))
else
  echo "  PASS: missing asset 404 response does not have immutable Cache-Control"
  passes=$((passes + 1))
fi
assert_contains "missing asset retains X-Content-Type-Options" "X-Content-Type-Options: nosniff" "$missing_headers"
assert_contains "missing asset retains CSP" "Content-Security-Policy:" "$missing_headers"

# Test 8: Unhashed root static asset (/solux/favicon.ico) does NOT get immutable cache
echo "Test 8: Unhashed static asset does not receive immutable header"
icon_headers="$(curl -sI "http://127.0.0.1:$PORT/solux/favicon.ico")"
assert_contains "favicon returns 200" "HTTP/1.1 200 OK" "$icon_headers"
if [[ "$icon_headers" == *"immutable"* ]]; then
  echo "  FAIL: favicon should not be marked immutable"
  failures=$((failures + 1))
else
  echo "  PASS: favicon is not marked immutable"
  passes=$((passes + 1))
fi

# Test 9: Gzip compression on JS asset with Accept-Encoding: gzip
echo "Test 9: Gzip compression on JS asset with Accept-Encoding: gzip"
gzip_headers="$(curl -sI -H "Accept-Encoding: gzip" "http://127.0.0.1:$PORT/solux/assets/index-Vew5OthO.js")"
assert_contains "returns 200 OK for gzipped JS" "HTTP/1.1 200 OK" "$gzip_headers"
assert_contains "JS asset returns Content-Encoding gzip" "Content-Encoding: gzip" "$gzip_headers"
assert_contains "Vary header includes Accept-Encoding" "Vary: Accept-Encoding" "$gzip_headers"

echo ""
echo "Test results: $passes passed, $failures failed"
if [ "$failures" -gt 0 ]; then
  exit 1
fi
