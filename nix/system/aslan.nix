{ lib, ... }:
let
  serverRoot = ../../system/hetzner;
  etcRoot = "${serverRoot}/etc";
  webRoot = "${serverRoot}/www/data";

  etcFiles = [
    "fail2ban/jail.d/nginx.local"
    "fail2ban/jail.d/sshd.local"
    "fail2ban/jail.local"
    "grafana.ini"
    "nginx/conf.d/calibre-server.conf"
    "nginx/conf.d/grafana.conf"
    "nginx/conf.d/infotb.conf"
    "nginx/conf.d/jellyfin.conf"
    "nginx/conf.d/laura-web.conf"
    "nginx/conf.d/lavish.conf"
    "nginx/conf.d/oauth.conf"
    "nginx/conf.d/plex.conf"
    "nginx/conf.d/solux.conf"
    "nginx/nginx.conf"
    "nginx/snippets/lavish-proxy-headers.conf"
    "nginx/snippets/lavish-response-headers.conf"
    "prometheus/prometheus.yml"
    "ssh/sshd_config.d/99-archnet-hardening.conf"
    "sysctl.d/99-archnet-security.conf"
    "systemd/system/calibre-server.service.d/override.conf"
    "systemd/system/fail2ban.service.d/override.conf"
    "systemd/system/minikube.service"
    "systemd/system/port-fwd-prometheus.service"
  ];

  webFiles = [
    "index.css"
    "index.html"
    "error/301.html"
    "error/400.html"
    "error/404.html"
    "error/500.html"
    "error/502.html"
    "error/503.html"
    "error/504.html"
  ];

  etcEntries = lib.genAttrs etcFiles (relativePath: {
    source = "${etcRoot}/${relativePath}";
    mode = if relativePath == "grafana.ini" then "0640" else "0644";
    group = if relativePath == "grafana.ini" then "grafana" else "root";
  });

  webRules = map (relativePath: let
    mode = if lib.hasSuffix ".css" relativePath then "0644" else "0644";
  in "C+ /www/data/${relativePath} ${mode} root root - ${webRoot}/${relativePath}") webFiles;

in
{
  # System Manager targets existing systemd Linux distributions. It does not
  # own the kernel, bootloader, native packages, service data, or networking.
  nixpkgs.hostPlatform = "x86_64-linux";

  environment.etc = etcEntries;

  systemd.tmpfiles.rules = [
    "d /www 0755 root root -"
    "d /www/data 0755 root root -"
    "d /www/data/error 0755 root root -"
  ] ++ webRules;
}
