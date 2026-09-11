# Upstream Native Subpath Migration: Job Applier & Lavish

## Context & Problem Statement

Currently, both **Job Applier** (`/etc/nginx/conf.d/job-applier.conf`) and **Lavish** (`/etc/nginx/conf.d/lavish.conf`) are mounted under subpaths (`/job-applier/` and `/lavish/`) on `aslan.archnet.lol` using runtime payload rewriting via Nginx's `ngx_http_sub_module` (`sub_filter`).

### Architectural Risks & Inefficiencies

1. **Disabled Upstream Compression**: To perform string substitutions across HTTP response bodies, Nginx must disable upstream compression by setting `proxy_set_header Accept-Encoding "";`. This causes backend services to return uncompressed HTML, JS, and JSON, significantly inflating bandwidth consumption and Time to First Byte (TTFB).
2. **Fragile Runtime Replacements**: `sub_filter` uses string/regex matching (e.g. `sub_filter '"/api/' '"/job-applier/api/';`, `sub_filter 'src="/artifact/' 'src="/lavish/artifact/';`). Dynamic JavaScript path constructions, template literals (`` `/api/${id}` ``), and minified or escaped strings easily bypass these static filters, causing broken routing or missing assets.
3. **Proxy Performance Overhead**: Nginx must inspect and rewrite every streaming response chunk in CPU memory before forwarding it to the client.

Migrating both applications to **native subpath awareness** eliminates runtime rewriting entirely, restores end-to-end gzip compression, and simplifies Nginx reverse-proxy configuration.

---

## Part 1: Job Applier Migration

Repository: [https://github.com/ervinpopescu/job-applier](https://github.com/ervinpopescu/job-applier)  
Upstream Port: `127.0.0.1:8001` (Docker Compose)

### 1.1 Backend Configuration (FastAPI)

FastAPI natively supports mounting behind reverse proxies with a path prefix via `root_path`:

1. **Application Definition**:

   ```python
   # main.py
   import os

   ROOT_PATH = os.getenv("ROOT_PATH", "/job-applier")

   app = FastAPI(
       title="Job Applier API",
       root_path=ROOT_PATH,
       docs_url="/docs",
       openapi_url="/openapi.json",
   )
   ```

2. **Uvicorn / Runner Ingress**:
   Pass `--root-path /job-applier` to Uvicorn in Dockerfile or Docker Compose:

   ```yaml
   command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --root-path /job-applier --proxy-headers --forwarded-allow-ips "*"
   ```

3. **Swagger UI & OpenAPI Docs**:
   With `root_path` configured, FastAPI automatically prefixes OpenAPI schema URLs and Swagger asset endpoints with `/job-applier`.

### 1.2 Frontend Configuration (Angular / Vite SPA)

1. **Base Href & Router Prefix**:
   Ensure `<base href="/job-applier/">` is set at build time or specified dynamically:
   - For Angular (`angular.json` / build command):

     ```bash
     ng build --base-href /job-applier/
     ```

   - For Vite (`vite.config.ts`):

     ```typescript
     export default defineConfig({
       base: process.env.BASE_PATH || '/job-applier/',
       // ...
     });
     ```

2. **API Client & Static Assets**:
   - Avoid hardcoding root-relative paths like `fetch('/api/...')` or `src="/files/..."`.
   - Use relative paths `api/...` or an environment variable `BASE_URL` (e.g. `const API_BASE = import.meta.env.BASE_URL + 'api'`).

### 1.3 Target Nginx Configuration (`conf.d/job-applier.conf`)

Once upstream natively prefixes routes, `conf.d/job-applier.conf` simplifies to a standard proxy without `sub_filter` and with gzip restored:

```nginx
# Redirect root/vanity shortcuts to canonical subpath
location = /jobs {
    return 301 /job-applier/;
}

location = /jobs/ {
    return 301 /job-applier/;
}

location = /job-applier {
    return 301 /job-applier/;
}

location ^~ /job-applier/ {
    proxy_pass http://127.0.0.1:8001;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Prefix /job-applier;

    # WebSocket / SSE support
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    # Timeouts & buffering
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_buffering off;
    client_max_body_size 64M;

    # Security & CSP headers
    include /etc/nginx/snippets/security-headers.conf;
}
```

---

## Part 2: Lavish Migration

Upstream Port: `127.0.0.1:4387`

### 2.1 Asset & Client Script Base Path

1. **Bundler Base Path**:
   Configure the build tool to output assets relative to `/lavish/`:

   ```javascript
   // vite.config.js or webpack.config.js
   export default {
     base: '/lavish/',
   };
   ```

2. **Client SDK & Chrome Assets**:
   Update `chrome-client.js`, `sdk.js`, and `whiteboard-frame` references:
   - Ensure the SDK emits artifact and session paths under `/lavish/artifact/` and `/lavish/events/`.
   - Update `chrome.css` and JavaScript bundles to request `/lavish/...` URLs natively.

### 2.2 WebSocket & Event Subpath Routing

- Ensure live streaming / session event WebSockets connect directly to `wss://$host/lavish/session/...`.
- Verify the server handles `/lavish/session/` directly without requiring path stripping.

### 2.3 Target Nginx Configuration (`conf.d/lavish.conf`)

Once upstream emits native subpaths, the six separate `location` blocks and response rewrites collapse into a single unified reverse proxy:

```nginx
location = /lavish {
    return 301 /lavish/;
}

location ^~ /lavish/ {
    proxy_pass http://127.0.0.1:4387;
    proxy_http_version 1.1;

    include /etc/nginx/snippets/lavish-proxy-headers.conf;
    include /etc/nginx/snippets/lavish-response-headers.conf;

    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

---

## Migration Rollout Checklist

- [ ] **Phase A: Upstream Job Applier**
  - [ ] Add `ROOT_PATH` support in FastAPI application.
  - [ ] Update frontend build base path to `/job-applier/`.
  - [ ] Deploy container to port `8001`.
  - [ ] Remove `sub_filter` and restore `Accept-Encoding` in `conf.d/job-applier.conf`.
  - [ ] Validate dashboard, API endpoints, file downloads, and PDF viewer.
- [ ] **Phase B: Upstream Lavish**
  - [ ] Configure asset base path to `/lavish/`.
  - [ ] Update SDK and Chrome client scripts to reference `/lavish/` endpoints.
  - [ ] Deploy service to port `4387`.
  - [ ] Remove `sub_filter` blocks from `conf.d/lavish.conf`.
  - [ ] Validate session recording, live artifacts, and whiteboard frame.
- [ ] **Phase C: Observability & Benchmarks**
  - [ ] Verify gzip compression is active via `curl -I -H "Accept-Encoding: gzip" https://aslan.archnet.lol/job-applier/`.
  - [ ] Monitor structured JSON logs in `/var/log/nginx/access.json.log` for response latency improvements.
