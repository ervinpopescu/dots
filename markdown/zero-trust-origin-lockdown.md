# Zero-Trust Direct-Origin Access Restriction: Hetzner (`aslan.archnet.lol`)

## 1. Executive Summary & Threat Model

Reverse-proxy architectures backed by Cloudflare (WAF, DDoS mitigation, rate limiting, Cloudflare Access Zero Trust) remain vulnerable if the origin server accepts direct TCP connections to its public IP address.

```text
Attacker ──[ Direct IP / Bypass Cloudflare ]──► Hetzner Public IP (Port 80/443) ──► Nginx (Unprotected)
                                                                                     │
Legitimate ──► Cloudflare Edge (WAF, Access, DDoS) ──► Hetzner Origin ───────────────┘
```

### Attack Vectors Addressed

1. **Direct-Origin IP Exposure & Scanning**: Internet-wide scanners (Censys, Shodan, BinaryEdge) scan public IPv4/IPv6 ranges on ports 80 and 443. Once the server's public IP is discovered, attackers can probe endpoints directly without triggering Cloudflare WAF rules or rate limiting.
2. **Access Control Bypass**: Services relying on edge authentication (such as Calibre or SFTP Viewer) can be attacked directly if edge enforcement is not paired with origin-level identity verification.
3. **Origin Denial-of-Service**: An adversary who identifies the direct origin IP can launch volumetric Layer 4 or Layer 7 floods directly at Hetzner's uplink, bypassing Cloudflare's edge DDoS mitigation.
4. **Historical IP & Certificate Leakage**: Historical DNS records, Certificate Transparency (CT) logs, and outbound server connections (such as webhooks or SMTP) can leak origin IP addresses.

### Objective

Lock down origin ingress on `aslan.archnet.lol` so that **all** public web traffic must be cryptographically authenticated or physically routed through the Cloudflare edge, while maintaining out-of-band management access for administration.

---

## 2. Assessment of Current Host Architecture

The Hetzner host (`aslan.archnet.lol`) runs an integrated server environment with specific operational constraints:

### 2.1 Private Management Overlay (Tailscale)

- **Status**: Tailscale is installed and actively connected (`tailscale0` interface, IP `100.118.210.41`).
- **Advantage**: Administrative services (SSH on TCP/22, Prometheus scrape endpoints, internal monitoring) can be accessed privately over Tailscale. Public SSH access can be completely decoupled from the public Hetzner interface, eliminating lockout risks during firewall transitions.

### 2.2 Dynamic Virtualization & Container Networking

- **Docker**: Active Docker bridge (`docker0`, `br-67d35a62208e`) with custom iptables chains (`DOCKER`, `DOCKER-USER`, `DOCKER-FORWARD`). Docker dynamically injects NAT and forward rules.
- **Libvirt / KVM**: Running virtual bridges (`virbr0`, `virbr1`) with dynamic DHCP, DNS (`dnsmasq`), and NAT rules.
- **Fail2ban**: Active `f2b-table` in `nftables` monitoring SSH and Nginx logs.

**Constraint**: Any firewall-level origin lockdown (Option C) must operate within `nftables` without overriding or flushing Docker's `DOCKER-USER` chain or Libvirt's network hooks.

---

## 3. Comparison of Ingress Lockdown Options

| Dimension | Option A: Cloudflare Tunnel (`cloudflared`) | Option B: Authenticated Origin Pulls (mTLS) | Option C: Firewall CIDR Filtering (`nftables`) |
| --- | --- | --- | --- |
| **Mechanism** | Outbound tunnel over QUIC/HTTPS | TLS client-certificate validation in Nginx | Packet filter drops non-CF IPs on 80/443 |
| **Open Public Ports** | **Zero** (All inbound 80/443 closed) | Inbound 443 open; drops unauthenticated TLS | Inbound 80/443 open only to Cloudflare CIDRs |
| **Origin IP Exposure** | Completely shielded (DNS is CNAME to tunnel) | Exposed, but TCP/TLS rejected | Exposed, but SYN packets dropped |
| **Certificate Management** | Managed automatically by Cloudflare Edge | Origin needs TLS cert + Cloudflare Pull CA | Origin must maintain Let's Encrypt / Origin CA |
| **Host Dependencies** | `cloudflared` systemd service | Standard Nginx configuration | `nftables` configuration & periodic CIDR sync |
| **Docker/Libvirt Risk** | **None** (pure user-space egress tunnel) | **None** (pure Nginx TLS layer) | Low–Moderate (requires careful rule ordering) |
| **Implementation Effort** | Medium (install binary, create tunnel, DNS) | **Low** (enable in dashboard, add 2 Nginx lines) | Low–Medium (nftables ruleset integration) |

---

## 4. Option A (Recommended Long-Term): Cloudflare Tunnel (`cloudflared`)

Cloudflare Tunnel creates private, outbound-only connections from the Hetzner host to Cloudflare data centers. Inbound public ports (80 and 443) are completely closed in the firewall.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Hetzner Origin Host (aslan.archnet.lol)                                 │
│                                                                        │
│   Nginx (127.0.0.1:443 / 127.0.0.1:80)                                │
│       ▲                                                                │
│       │ (local loopback)                                               │
│   cloudflared (systemd service)                                        │
│       │                                                                │
│       └─── Outbound QUIC/HTTPS (UDP 7844 / TCP 443) ──┐                │
└───────────────────────────────────────────────────────┼────────────────┘
                                                        │
                                                        ▼
                                           Cloudflare Edge Anycast
                                                        ▲
                                                        │
                                                 Public Clients
```

### 4.1 Prerequisites & Installation

1. Install `cloudflared` on Arch Linux:

   ```bash
   sudo pacman -S cloudflared
   ```

2. Authenticate the tunnel CLI with your Cloudflare account:

   ```bash
   cloudflared tunnel login
   ```

### 4.2 Tunnel Creation & Configuration

1. Create a dedicated origin tunnel:

   ```bash
   cloudflared tunnel create aslan-origin
   ```

   This generates a tunnel UUID and credentials JSON file at `/etc/cloudflared/<TUNNEL_UUID>.json`.

2. Create the configuration file `/etc/cloudflared/config.yml`:

   ```yaml
   tunnel: <TUNNEL_UUID>
   credentials-file: /etc/cloudflared/<TUNNEL_UUID>.json

   ingress:
     # Aslan main virtual host
     - hostname: aslan.archnet.lol
       service: https://127.0.0.1:443
       originRequest:
         originServerName: aslan.archnet.lol
         caPool: /etc/letsencrypt/live/aslan.archnet.lol/fullchain.pem

     # SFTP Viewer dedicated host
     - hostname: sftp.archnet.lol
       service: https://127.0.0.1:443
       originRequest:
         originServerName: sftp.archnet.lol
         caPool: /etc/ssl/certs/sftp.archnet.lol-origin.pem

     # Laura Photography dedicated virtual host
     - hostname: laura-photos.com
       service: https://127.0.0.1:443
       originRequest:
         originServerName: laura-photos.com
         noTLSVerify: true # or caPool if using origin cert

     - hostname: www.laura-photos.com
       service: https://127.0.0.1:443
       originRequest:
         originServerName: www.laura-photos.com
         noTLSVerify: true

     # Default catch-all rule (required by cloudflared)
     - service: http_status:404
   ```

3. Route DNS records to the tunnel:

   ```bash
   cloudflared tunnel route dns aslan-origin aslan.archnet.lol
   cloudflared tunnel route dns aslan-origin sftp.archnet.lol
   cloudflared tunnel route dns aslan-origin laura-photos.com
   cloudflared tunnel route dns aslan-origin www.laura-photos.com
   ```

4. Enable and start the systemd service:

   ```bash
   sudo systemctl enable --now cloudflared
   ```

5. **Firewall Lockdown**: Once verified, close inbound ports 80 and 443 on the public interface (`eth0`). No public web ports remain exposed.

---

## 5. Option B: Cloudflare Authenticated Origin Pulls (AOP / mTLS)

Authenticated Origin Pulls enforces Mutual TLS (mTLS) between Cloudflare's edge and Nginx. During the TLS handshake on port 443, Nginx requests and verifies a client certificate presented by Cloudflare. Any direct connection to the server's IP cannot complete the handshake and is rejected immediately at TLS negotiation.

```text
Client ──[ Direct IP:443 ]──► Nginx (Requires Client Cert) ──► TLS Handshake Failed (400 Bad Request / Dropped)
Client ──► Cloudflare Edge ──► Nginx (Presents CF Client Cert) ──► Verified ──► Request Served
```

### 5.1 Cloudflare Dashboard Activation

1. Navigate to **Cloudflare Dashboard** → Select Domain (`archnet.lol` / `laura-photos.com`).
2. Go to **SSL/TLS** → **Origin Server**.
3. Toggle **Authenticated Origin Pulls** to **ON**.

### 5.2 Nginx Configuration

1. Download the official Cloudflare Authenticated Origin Pull CA certificate:

   ```bash
   sudo curl -fsSL -o /etc/ssl/certs/cloudflare-origin-pull-ca.pem \
     https://developers.cloudflare.com/ssl/static/authenticated_origin_pull_ca.pem
   sudo chmod 644 /etc/ssl/certs/cloudflare-origin-pull-ca.pem
   ```

2. Create a reusable snippet `/etc/nginx/snippets/cloudflare-origin-pull.conf`:

   ```nginx
   # Cloudflare Authenticated Origin Pulls (mTLS)
   # Enforce that inbound TLS connections present a valid client certificate
   # signed by Cloudflare's Origin Pull Certificate Authority.
   ssl_client_certificate /etc/ssl/certs/cloudflare-origin-pull-ca.pem;
   ssl_verify_client on;
   ```

3. Include the snippet in protected HTTPS server blocks in `nginx.conf`:

   ```nginx
   server {
       listen 443 ssl default_server;
       http2 on;
       listen [::]:443 ssl default_server;
       server_name aslan.archnet.lol;

       include /etc/nginx/snippets/cloudflare-origin-pull.conf;
       # ... remaining configuration ...
   }

   server {
       listen 443 ssl;
       http2 on;
       listen [::]:443 ssl;
       server_name laura-photos.com www.laura-photos.com;

       include /etc/nginx/snippets/cloudflare-origin-pull.conf;
       # ... remaining configuration ...
   }
   ```

4. Test and reload Nginx:

   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### 5.3 Verification of Option B

- **Direct IP test**:

  ```bash
  curl -k -v https://<HETZNER_PUBLIC_IP>/
  ```

  *Expected Result*: TLS alert `handshake failure` or `400 Bad Request: No required SSL certificate was sent`.

- **Cloudflare Edge test**:

  ```bash
  curl -I https://aslan.archnet.lol
  ```

  *Expected Result*: HTTP `200 OK` or `302 Found`.

---

## 6. Option C: Direct Firewall CIDR Restriction (`nftables`)

If firewall-level packet dropping is preferred over TLS rejection, configure `nftables` to drop incoming traffic on ports 80 and 443 unless the source IP falls within Cloudflare's published IP ranges.

### 6.1 Cloudflare CIDR IP Sets

Cloudflare's official ranges (aligned with `snippets/cloudflare-realip.conf`):

- **IPv4**:
  `173.245.48.0/20`, `103.21.244.0/22`, `103.22.200.0/22`, `103.31.4.0/22`, `141.101.64.0/18`, `108.162.192.0/18`, `190.93.240.0/20`, `188.114.96.0/20`, `197.234.240.0/22`, `198.41.128.0/17`, `162.158.0.0/15`, `104.16.0.0/13`, `104.24.0.0/14`, `172.64.0.0/13`, `131.0.72.0/22`
- **IPv6**:
  `2400:cb00::/32`, `2606:4700::/32`, `2803:f800::/32`, `2405:b500::/32`, `2405:8100::/32`, `2a06:98c0::/29`, `2c0f:f248::/32`

### 6.2 `nftables` Configuration Ruleset

Create `/etc/nftables.d/cloudflare-ingress.nft`:

```nft
table inet cloudflare_lockdown {
    set cloudflare_ipv4 {
        type ipv4_addr
        flags interval
        elements = {
            173.245.48.0/20, 103.21.244.0/22, 103.22.200.0/22,
            103.31.4.0/22, 141.101.64.0/18, 108.162.192.0/18,
            190.93.240.0/20, 188.114.96.0/20, 197.234.240.0/22,
            198.41.128.0/17, 162.158.0.0/15, 104.16.0.0/13,
            104.24.0.0/14, 172.64.0.0/13, 131.0.72.0/22
        }
    }

    set cloudflare_ipv6 {
        type ipv6_addr
        flags interval
        elements = {
            2400:cb00::/32, 2606:4700::/32, 2803:f800::/32,
            2405:b500::/32, 2405:8100::/32, 2a06:98c0::/29,
            2c0f:f248::/32
        }
    }

    chain ingress_filter {
        type filter hook input priority filter - 5; policy accept;

        # Always accept loopback and private Tailscale traffic
        iifname "lo" accept
        iifname "tailscale0*" accept

        # Accept established and related traffic
        ct state established,related accept

        # Allow web ports (80, 443) only from verified Cloudflare ranges
        ip saddr @cloudflare_ipv4 tcp dport { 80, 443 } accept
        ip6 saddr @cloudflare_ipv6 tcp dport { 80, 443 } accept

        # Drop all other direct ingress attempts to web ports
        tcp dport { 80, 443 } counter drop
    }
}
```

### 6.3 Safe Application Procedure

To apply without risking network lockout or conflicting with Docker/Libvirt:

1. **Verify Out-of-Band SSH**: Ensure an active SSH connection is open over Tailscale (`ssh user@100.118.210.41`).
2. **Atomic Load with Rollback Timeout**:

   ```bash
   sudo nft -f /etc/nftables.d/cloudflare-ingress.nft && sleep 30 && sudo nft delete table inet cloudflare_lockdown
   ```

   If testing succeeds over Cloudflare within 30 seconds, persist the configuration.

---

## 7. Recommended Rollout Strategy

A three-phase migration provides immediate security without operational disruption:

```text
[ Phase 1: Immediate ] ──► [ Phase 2: Boundary Hardening ] ──► [ Phase 3: Zero-Ingress Architecture ]
Option B: Enable AOP/mTLS    Option C: nftables Cloudflare       Option A: Cloudflare Tunnel
in Cloudflare & Nginx        CIDRs drop direct port 80/443       Close all public ports on eth0
```

1. **Phase 1 (Immediate — Lowest Risk, Zero Downtime)**:
   - Enable Cloudflare Authenticated Origin Pulls (**Option B**).
   - Drop `ssl_client_certificate` and `ssl_verify_client on;` into Nginx.
   - Any scanner or bot attempting direct IP connection on port 443 fails at TLS handshake.
2. **Phase 2 (Hardening)**:
   - Apply the `nftables` CIDR filter (**Option C**) to drop unauthenticated port 80/443 probes before they reach Nginx worker processes.
   - Restrict public SSH on port 22 to Tailscale only, binding `sshd` to `tailscale0` or dropping non-Tailscale port 22 packets.
3. **Phase 3 (Strategic Evolution)**:
   - Deploy `cloudflared` (**Option A**).
   - Close ports 80 and 443 completely on the Hetzner public firewall.
   - Origin IP is fully decoupled from public routing.

---

## 8. Safe Verification Checklist

Before and after enabling origin restrictions, run the following verification checks:

- [ ] **Tailscale SSH Continuity**: Confirm SSH access via `100.118.210.41` is functional.
- [ ] **Direct IP Web Test**:

  ```bash
  curl -k -I --connect-timeout 5 https://<HETZNER_PUBLIC_IP>/
  ```

  *Pass criteria*: Connection timed out, connection refused, or SSL handshake error.
- [ ] **Cloudflare Hostname Ingress**:

  ```bash
  curl -I https://aslan.archnet.lol
  curl -I https://laura-photos.com
  curl -I https://sftp.archnet.lol
  ```

  *Pass criteria*: All return valid HTTP responses (200 / 301 / 302).
- [ ] **Docker Bridge Connectivity**: Confirm outbound and internal container communication (Job Applier on port 8001) is unaffected.
- [ ] **Libvirt VM Ingress/Egress**: Confirm VM bridges (`virbr0`, `virbr1`) maintain external DNS and NAT routing.
