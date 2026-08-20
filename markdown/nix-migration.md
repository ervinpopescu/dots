# Nix migration

This repository is moving from chezmoi to a pinned Nix flake while keeping the
existing operating systems:

- Linux hosts remain on their current distributions.
- Home Manager owns user packages, dotfiles, development tools, and coding
  agents.
- nix-darwin integrates the MacBook system configuration.
- System Manager owns the migrated Aslan `/etc` and systemd runtime files.
- `archnet-cfg` remains responsible for installation, bootstrap, disk/data
  migration, and other destructive setup.

The migration is intentionally staged. Do not activate a Home Manager or
System Manager output until its destination has been reviewed and backed up.
Use the [Nix operations runbook](./nix-operations.md) for exact preflight,
activation, validation, and recovery commands.

## Outputs

```text
homeConfigurations.ervin@lenovo
homeConfigurations.ervin@cloudtop
homeConfigurations.ervin@hp
homeConfigurations.ervin@aslan
homeConfigurations.ervin@macbook-apple-silicon

darwinConfigurations.macbook-apple-silicon
systemConfigs.aslan
systemConfigs.default  # Aslan-only System Manager CLI alias
```

The MacBook output is Apple Silicon only. Linux output names refer to the
existing host/profile names; they do not imply NixOS. `systemConfigs.default`
is an Aslan-only alias required by the System Manager CLI; use the named
`systemConfigs.aslan` output for explicit Nix builds.

## Bootstrap

Install Nix with flakes enabled using the official multi-user installer or a
trusted distribution-specific installer. Then validate the committed flake:

```bash
nix flake check
```

`flake.lock` is committed and is the dependency pin. Do not update it during a
host migration; use a dedicated, reviewed dependency-update change instead.

## Home Manager

See the [Nix operations runbook](./nix-operations.md) for backup-aware first
activation and rollback. The short commands below are architecture examples,
not a substitute for its preflight checklist.

On Linux, use standalone Home Manager:

```bash
nix run github:nix-community/home-manager -- \
  switch --flake .#ervin@lenovo
```

Replace `lenovo` with `hp` or `aslan` on those hosts. Home Manager currently
owns the shared developer baseline, coding-agent configuration, and the Lenovo
Transmission module. Desktop configuration remains native during the staged
cutover to avoid duplicate pacman/Nix binaries.

Cloudtop targets the invoking account's existing `$HOME`; it never assumes or
creates `/home/ervin`. Its configuration therefore requires impure evaluation:

```bash
nix run github:nix-community/home-manager -- \
  switch --impure --flake .#ervin@cloudtop
```

Run this only as the intended Cloudtop account after confirming `$HOME` is its
actual existing home directory.

On macOS, use nix-darwin, which integrates the same Home Manager modules:

```bash
darwin-rebuild switch --flake .#macbook-apple-silicon
```

Only Apple Silicon MacBook activation is currently supported.

## System Manager on Aslan

System Manager is deliberately limited to the active runtime files already
migrated from `archnet-cfg`. It does not manage the kernel, bootloader, native
package database, service data, or networking setup.

Review the generated configuration first:

```bash
nix build .#systemConfigs.aslan
nix run github:numtide/system-manager -- \
  switch --flake . --sudo
```

System Manager's CLI consumes `systemConfigs.default`, which is an Aslan-only
alias for the named `systemConfigs.aslan` build. Its CLI does not yet implement
rollback, so retain verified root-level backups and the legacy deploy hook
until a reversible test is completed.

Before replacing the existing sudo deployment hook on Aslan, validate:

```bash
sudo nginx -t
sudo fail2ban-client -t
sudo sshd -t
sudo promtool check config /etc/prometheus/prometheus.yml
sudo systemd-analyze verify
```

The old `run_after_system-deploy.sh.tmpl` remains as a transitional fallback
until this validation succeeds. `archnet-cfg` must not deploy any path owned by
`systemConfigs.aslan`.

## Secrets

Encrypted secrets use sops-nix. The Lenovo Transmission password belongs in
`secrets/lenovo.yaml`, not in the Nix store or a plaintext template:

```bash
sops secrets/lenovo.yaml
```

The Home Manager Lenovo module enables Transmission only after that encrypted
file exists. Authentication, browser state, agent sessions, caches, and plugin
download trees remain runtime state and are not declaratively copied.

## Migration boundary

The legacy chezmoi files remain in the tree during the staged cutover so that
existing machines can be recovered. A destination must be excluded from
chezmoi immediately before Home Manager owns it; the final cleanup will remove
`.chezmoi.toml.tmpl`, `.chezmoiignore`, apply hooks, and `pkgs` only after all
five profiles have been activated and verified.
