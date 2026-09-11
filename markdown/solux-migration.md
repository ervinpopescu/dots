# Solux Hosting Migration Runbook: Node Preview Daemon to Static Nginx

## Context

Solux was previously hosted on Hetzner (`aslan`) via a reverse proxy in `/etc/nginx/conf.d/solux.conf` forwarding requests to a user-level Vite preview server (`127.0.0.1:4173`) managed by `solux.service`.

This migration moves Solux to direct static hosting served by Nginx from `/var/www/solux` with:

- `root /var/www;` for `/solux/` subpath resolution
- Canonical 301 redirect for `/solux` -> `/solux/`
- SPA fallback to `/solux/index.html`
- Immutable caching (`Cache-Control: public, max-age=31536000, immutable`) exclusively for content-hashed assets under `/solux/assets/`
- Strict revalidation (`Cache-Control: no-store, no-cache, must-revalidate`) for lifecycle files (`index.html`, `sw.js`, `registerSW.js`, `manifest.webmanifest`, `workbox-*.js`)
- Complete Solux-specific security headers and least-permissive Content Security Policy (CSP) defined in `/etc/nginx/snippets/solux-security-headers.conf` included in every location setting `add_header Cache-Control`
- Safe retirement of `solux.service`

## Rollout Sequence

Execute these steps in order when performing the live rollout:

### Step 1: Prepare `/var/www/solux` Directory

Create the target web root and grant write ownership to deploying user `ervin` with group `http`:

```bash
sudo mkdir -p /var/www/solux
sudo chown -R ervin:http /var/www/solux
sudo chmod -R u=rwX,go=rX /var/www/solux
```

### Step 2: Build and Deploy Static Files via `just deploy`

Use the tested `just deploy` recipe in the Solux repository to build the production bundle and atomically deploy to `/var/www/solux`:

```bash
cd /home/ervin/prjs/solux
just deploy
```

> **Note:** `just deploy` stages content-hashed assets before atomically moving lifecycle files (`manifest.webmanifest`, `sw.js`, `registerSW.js`, `index.html`), guaranteeing zero missing chunk 404s during active client navigation. To preview actions without writing, run `just deploy-check`.

### Step 3: Deploy Nginx Configurations and Reload

```bash
system-deploy.sh
# Validates syntax via `nginx -t` and reloads Nginx safely
```

### Step 4: Verify Deployment

Run production verification curl checks against `https://aslan.archnet.lol`:

```bash
# 1. Exact redirect: /solux -> /solux/ (301 Moved Permanently)
curl -sI https://aslan.archnet.lol/solux | grep -E "HTTP/|Location:"

# 2. Entrypoint HTML: 200 OK, no-store cache, and security headers
curl -sI https://aslan.archnet.lol/solux/ | grep -E "HTTP/|Cache-Control:|Strict-Transport-Security:|Content-Security-Policy:|X-Content-Type-Options:|X-Frame-Options:"

# 3. SPA route fallback: /solux/map returns index.html with no-store
curl -sI https://aslan.archnet.lol/solux/map | grep -E "HTTP/|Cache-Control:"

# 4. Lifecycle files: sw.js and manifest.webmanifest return no-store
curl -sI https://aslan.archnet.lol/solux/sw.js | grep -E "HTTP/|Cache-Control:"
curl -sI https://aslan.archnet.lol/solux/manifest.webmanifest | grep -E "HTTP/|Cache-Control:"

# 5. Hashed assets: immutable caching and gzip compression
ASSET=$(basename $(ls /var/www/solux/assets/*.js | head -n 1))
curl -sI -H "Accept-Encoding: gzip" https://aslan.archnet.lol/solux/assets/$ASSET | grep -E "HTTP/|Cache-Control:|Content-Encoding:|Vary:"

# 6. Missing asset: returns 404 without immutable Cache-Control
curl -sI https://aslan.archnet.lol/solux/assets/nonexistent-chunk.js | grep -E "HTTP/|Cache-Control:|X-Content-Type-Options:"
```

### Step 5: Retire User Systemd Service

Once static delivery is verified:

```bash
retire-solux-service.sh
```

Or manually:

```bash
systemctl --user stop solux.service
systemctl --user disable solux.service
rm -f ~/.config/systemd/user/solux.service
systemctl --user daemon-reload
```

## Rollback Procedure

If issues arise during cutover or verification fails, follow this rollback procedure:

### 1. Restore and Start User Service

Recreate `~/.config/systemd/user/solux.service`:

```ini
[Unit]
Description=Solux Web App
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ervin/prjs/solux
ExecStart=/home/ervin/.local/share/nvm/versions/node/v22.8.0/bin/npm run preview -- --port 4173 --host 127.0.0.1
Restart=on-failure
Environment=PATH=/home/ervin/.local/share/nvm/versions/node/v22.8.0/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
```

Reload the user daemon and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now solux.service
systemctl --user status solux.service
```

### 2. Revert Nginx Configuration

Restore `/etc/nginx/conf.d/solux.conf` to reverse-proxy mode:

```nginx
location ^~ /solux/ {
    proxy_pass http://127.0.0.1:4173/solux/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /solux {
    return 301 /solux/;
}
```

### 3. Test and Reload Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Verify Rollback

Confirm the preview reverse proxy is serving requests again:

```bash
curl -sI http://127.0.0.1:4173/solux/
curl -sI https://aslan.archnet.lol/solux/
```
