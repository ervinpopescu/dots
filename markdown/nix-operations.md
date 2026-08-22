# Nix operations runbook

This is the operational guide for the staged migration from chezmoi. It applies
only to the existing operating systems; it does **not** install NixOS or replace
pacman, Homebrew, the kernel, bootloader, networking, or service data.

Read this document before any activation. Home Manager, nix-darwin, and System
Manager refuse many unsafe changes, but an activation still changes the target
account or host.

## Current ownership

| Area                                                                              | Current owner             | Notes                                                                                               |
| --------------------------------------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------- |
| Shared CLI/developer packages                                                     | Home Manager              | Explicit package baseline only; legacy `pkgs` is not imported.                                      |
| Pi, Claude, Gemini, and shared agent instructions                                 | Home Manager              | Authentication, caches, sessions, and downloaded plugins remain runtime state.                      |
| Lenovo Transmission                                                               | Home Manager              | Only after the encrypted Lenovo secret is present.                                                  |
| Aslan `/etc`, `/www`, and selected systemd files                                  | System Manager output     | Do not activate until the Aslan checklist passes.                                                   |
| Alacritty, dunst, lf, nwg-launchers, systemd, VSCodium, X11, zathura, and `~/bin` | Home Manager              | Chezmoi ignores these destinations after the ownership handoff.                                     |
| Templated Zsh, Git, tmux, Neovim, Qtile, rofi, and related dotfiles               | chezmoi source material   | These remain transitional so template naming, modes, and secrets are not copied into the Nix store. |
| Cloudtop account and home directory                                               | Existing Cloudtop account | The profile reads the activating account's `$HOME`; it never assumes `/home/ervin`.                 |

Do not let chezmoi and Home Manager own the same destination. Immediately
exclude a destination from chezmoi when its Home Manager declaration is added.
Do not delete chezmoi metadata, apply hooks, or `pkgs` until all intended hosts
have completed the migration.

## Supported outputs

| Host     | Output                  | System           | Home path          | Special requirement                                 |
| -------- | ----------------------- | ---------------- | ------------------ | --------------------------------------------------- |
| Lenovo   | `ervin@lenovo`          | `x86_64-linux`   | `/home/ervin`      | Transmission secret is optional until configured.   |
| Cloudtop | `ervin@cloudtop`        | `x86_64-linux`   | activating `$HOME` | Every evaluation/build/switch needs `--impure`.     |
| HP       | `ervin@hp`              | `x86_64-linux`   | `/home/ervin`      | None.                                               |
| Aslan    | `ervin@aslan`           | `x86_64-linux`   | `/home/ervin`      | Home Manager and System Manager are separate steps. |
| MacBook  | `macbook-apple-silicon` | `aarch64-darwin` | `/Users/ervin`     | Apple Silicon only.                                 |

There is no Intel MacBook output. `systemConfigs.aslan` is the named build
output; `systemConfigs.default` is an alias used by the System Manager CLI and
must be switched only on Aslan.

## Bootstrap and repository preparation

1. Install Nix with flakes enabled using the official multi-user installer for
   the host. Do not run a system-wide installer on Cloudtop without the system
   administrator's approval.
2. Enable the required Nix experimental features persistently. On a
   multi-user installation, replace any existing `experimental-features` line
   with the required values, then restart the Linux daemon:

   ```bash
   sudo install -d -m 0755 /etc/nix
   sudo touch /etc/nix/nix.conf
   sudo sed -i -E \
     's/^[[:space:]]*experimental-features[[:space:]]*=.*/experimental-features = nix-command flakes/' \
     /etc/nix/nix.conf
   if ! sudo /usr/bin/grep -qE '^[[:space:]]*experimental-features[[:space:]]*=' /etc/nix/nix.conf; then
     printf '\nexperimental-features = nix-command flakes\n' | sudo tee -a /etc/nix/nix.conf
   fi
   sudo systemctl restart nix-daemon.service  # Linux only
   ```

   On macOS, use the same `/etc/nix/nix.conf` update and open a new shell; do
   not run the Linux `systemctl` command.

   On Arch, if the `nix` package is installed but `/nix/store` is missing,
   initialize the incomplete store once and enable the daemon at boot:

   ```bash
   sudo nix-store --init
   sudo systemctl enable --now nix-daemon.service
   ```

3. Confirm flakes work before continuing:

   ```bash
   nix --version
   nix flake --help >/dev/null
   nix config show | /usr/bin/grep '^experimental-features'
   ```

   As a temporary fallback only, pass
   `--extra-experimental-features 'nix-command flakes'` to every Nix command.

4. Clone this repository as the target user and enter it:

   ```bash
   git clone git@github.com:ervinpopescu/dots.git ~/src/dots
   cd ~/src/dots
   git switch migration/nix-home-manager
   git pull --ff-only
   ```

5. Before changing a host, create an external backup or snapshot of its home
   directory and retain the existing chezmoi source and generated state. For
   Aslan, also keep a root-level backup of every file to be handed to System
   Manager.

The committed `flake.lock` is the dependency pin. Do **not** run `nix flake
update` during a host migration. Update inputs only in a dedicated change,
then run the checks below and commit both `flake.nix` and `flake.lock`.

## Preflight and Home Manager build

Run the standard checks from the repository. They evaluate configuration but do
not activate it:

```bash
nix flake check --all-systems --no-build
nix build '.#homeConfigurations."ervin@lenovo".activationPackage'
nix run .#hm-preflight -- ervin@lenovo
```

`hm-preflight` reports path-level `ADD`, `CHANGE`, `COLLISION`, and `REMOVE`
operations without activation. It intentionally does not print file contents by
default. To request unified text diffs, acknowledge that existing local files
may contain secrets:

```bash
nix run .#hm-preflight -- ervin@lenovo --content
```

Substitute `lenovo` with `hp` or `aslan` for those Linux hosts. On Cloudtop,
first confirm that the target account has a real, existing home directory and
use impure evaluation:

```bash
test -n "$HOME" && test -d "$HOME"
printf 'Cloudtop target home: %s\n' "$HOME"
nix flake check --impure --all-systems --no-build
nix build --impure '.#homeConfigurations."ervin@cloudtop".activationPackage'
```

On the Apple Silicon MacBook, build without activation:

```bash
sudo nix run nix-darwin/master#darwin-rebuild -- \
  build --flake .#macbook-apple-silicon
```

The bootstrap `nix-darwin` command supplies only the rebuild CLI; the resulting
configuration still uses this repository's locked inputs. After the first
successful switch, use `sudo darwin-rebuild` from the installed profile.

## First Home Manager activation

Home Manager stops before changing anything when a managed file already exists.
The preferred response is to inspect that file and migrate any wanted settings.
After reviewing `hm-preflight`, use the repository's pinned switch wrapper:

```bash
nix run .#hm-switch -- ervin@lenovo
```

The wrapper uses Home Manager's custom backup command rather than an unmanaged
`-b` suffix. Each collision is renamed with a unique identifier and recorded in
a NUL-safe manifest below
`$XDG_STATE_HOME/home-manager/collision-backups` (or
`~/.local/state/home-manager/collision-backups`). Backup contents remain in the
home directory and never enter the Nix store.

Cloudtop must run the same operation as its intended account. The wrapper adds
`--impure` automatically for `ervin@cloudtop`:

```bash
test -n "$HOME" && test -d "$HOME"
nix run .#hm-preflight -- ervin@cloudtop
nix run .#hm-switch -- ervin@cloudtop
```

After each successful Linux activation, verify the managed commands and agent
files without changing authentication state:

```bash
command -v git zsh tmux nvim pi claude gemini
systemctl --user status --no-pager
```

Every generation created by this repository defers collision restoration during
forward activation. The `hm-switch` process remains available across the
activation and explicitly requests restoration after a rollback, including when
rolling back to a generation that predates the hook. Restoration reads every
backup manifest and restores a backup only when its original path is absent. If
the preceding generation still manages that path—or any file now exists
there—the backup is retained and never overwrites it.

```bash
home-manager generations
nix run .#hm-switch -- ervin@lenovo --rollback
```

The first-ever Home Manager generation has no preceding generation, so it
cannot use generation rollback. To abandon Home Manager entirely, run its
interactive uninstall and then restore paths made absent by uninstall:

```bash
home-manager uninstall
hm-restore-backups
```

## Apple Silicon MacBook activation and rollback

First build and run `hm-preflight` as above. The nix-darwin Home Manager module
uses the same manifest-recording backup command automatically; it does not use
the standalone `-b` option.

```bash
sudo nix run nix-darwin/master#darwin-rebuild -- \
  switch --flake .#macbook-apple-silicon
```

After bootstrap, use the installed wrapper for every switch and rollback:

```bash
darwin-switch --flake .#macbook-apple-silicon
sudo darwin-rebuild --list-generations
darwin-switch --rollback
```

The nix-darwin activation records the actual old and new Darwin system paths,
and `darwin-switch` runs restoration after the rebuild returns. The wrapper
therefore remains able to restore an eligible backup when the target generation
predates the restore hook. As on Linux, the first-ever generation has no earlier
generation to roll back to.

Confirm the current user remains `ervin` with home `/Users/ervin` before the
first switch. Do not use this output on an Intel Mac.

## Lenovo Transmission

Transmission is Lenovo-only. Before activation, install `sops` by a trusted
means and place the age private identity at:

```text
~/.config/sops/age/keys.txt
```

Create or edit the encrypted repository file:

```bash
sops secrets/lenovo.yaml
```

It must contain:

```yaml
transmission:
  rpc-password: replace-with-a-real-secret
```

Home Manager treats the Transmission settings symlink as a normal managed path,
so `hm-preflight` reports any existing file before activation and the manifest
backup mechanism preserves a collision. The rendered secret remains in the
runtime sops directory rather than the Nix store. To deliberately adopt the
Nix-generated settings, stop Transmission, inspect the preflight, and activate
with the repository wrapper:

```bash
systemctl --user stop transmission
nix run .#hm-preflight -- ervin@lenovo
nix run .#hm-switch -- ervin@lenovo
```

Then validate:

```bash
stat -c '%a %n' ~/.config/transmission-daemon/settings.json
systemctl --user restart transmission
systemctl --user status --no-pager transmission
```

A settings file created by Home Manager has mode `600`. Confirm Transmission is
bound as configured and that no Aslan Transmission service, Nginx proxy, or
server configuration is reintroduced.

## Aslan state bind mounts

Aslan keeps application state on the large native ext4 RAID1 data filesystem.
The filesystem layout and `/etc/fstab` remain distro-owned; System Manager does
not manage these service-data mounts. The following bind mounts prevent
Minikube, Docker, and containerd state from filling the root filesystem:

| Source on `/mnt/data`                   | Runtime path                        |
| --------------------------------------- | ----------------------------------- |
| `/mnt/data/system-state/minikube-ervin` | `/home/ervin/.local/share/minikube` |
| `/mnt/data/system-state/minikube-root`  | `/root/.minikube`                   |
| `/mnt/data/system-state/docker`         | `/var/lib/docker`                   |
| `/mnt/data/system-state/containerd`     | `/var/lib/containerd`               |

The persistent `/etc/fstab` entries are:

```fstab
/mnt/data/system-state/minikube-ervin /home/ervin/.local/share/minikube none bind,x-systemd.requires-mounts-for=/mnt/data/system-state/minikube-ervin 0 0
/mnt/data/system-state/minikube-root /root/.minikube none bind,x-systemd.requires-mounts-for=/mnt/data/system-state/minikube-root 0 0
/mnt/data/system-state/docker /var/lib/docker none bind,x-systemd.requires-mounts-for=/mnt/data/system-state/docker 0 0
/mnt/data/system-state/containerd /var/lib/containerd none bind,x-systemd.requires-mounts-for=/mnt/data/system-state/containerd 0 0
```

`x-systemd.requires-mounts-for` ensures `/mnt/data` is available before the
binds. Do not add `nofail`: starting a service against an empty fallback path on
`/` would create split state. Before changing these mounts, stop the Ervin user
Minikube unit, both Minikube VMs, Docker, and containerd; copy state with
`rsync -aHAXS --numeric-ids`; verify a dry run has no differences; and retain a
copy of `/etc/fstab` outside the edited path until validation succeeds.

QEMU runs as `libvirt-qemu`. The Aslan Home Manager profile grants that account
execute-only traversal ACLs on `$HOME/.local` and `$HOME/.local/share`; it does
not grant directory listing or file read access. Verify the final state with:

```bash
for path in \
  /home/ervin/.local/share/minikube \
  /root/.minikube \
  /var/lib/docker \
  /var/lib/containerd; do
  sudo findmnt "$path"
done
getfacl -cp ~/.local ~/.local/share
sudo docker info --format 'root={{.DockerRootDir}} images={{.Images}}'
systemctl --user status --no-pager minikube.service
sudo virsh list --all
```

The first migration recovered about 105 GiB on `/dev/md2`. Its rollback copy is
`/etc/fstab.before-state-bind-20260822151533`. The `prod` KVM disks opened from
the new bind mount after applying the ACL, but the existing two-node cluster did
not complete startup because its SSH handshake reset while the worker remained
off. It was left enabled but cleanly stopped; resolve that cluster-level issue
before treating Minikube as healthy.

## Aslan System Manager cutover

System Manager is limited to the files described by `nix/system/aslan.nix`; it
does not own packages, service data, the kernel, bootloader, or networking.

1. Make and verify root-owned backups of all affected Aslan paths.
2. Build the named configuration without activation:

   ```bash
   nix build .#systemConfigs.aslan
   ```

3. Review the source diff and generated plan. Do not remove the legacy
   `run_after_system-deploy.sh.tmpl` yet.
4. On **Aslan only**, use System Manager's standard default output:

   ```bash
   nix run github:numtide/system-manager -- \
     switch --flake . --sudo
   ```

5. Immediately validate:

   ```bash
   sudo nginx -t
   sudo fail2ban-client -t
   sudo sshd -t
   sudo promtool check config /etc/prometheus/prometheus.yml
   sudo systemd-analyze verify
   ```

6. Only after those checks and route/service checks pass should the old sudo-copy
   hook be retired.

**Important:** System Manager currently creates generations but its CLI does
not implement rollback. Keep the pre-switch root backups and the legacy deploy
path until a reversible Aslan test has been performed and documented. Never
activate this output on Lenovo, Cloudtop, HP, or the MacBook.

## Rust toolchains

Home Manager installs the pinned Nix `rustup` launcher, not a fixed Nix
`rustc`/`cargo` toolchain. Rustup manages its own toolchains, components, and
cargo-installed binaries as user runtime state; they remain outside Git and are
not deleted by Home Manager rollback.

After the first Home Manager activation, install the desired baseline:

```bash
rustup toolchain install stable
rustup default stable
rustup component add rustfmt clippy rust-analyzer
```

Use a project-specific `rust-toolchain.toml` when a project needs a different
compiler version. Do not run rustup commands from a Home Manager activation,
since they download mutable network state.

## Ongoing maintenance

For any intentional Nix change:

```bash
nix fmt
nix flake check --all-systems --no-build
```

For an intentional dependency update, work on a branch:

```bash
nix flake update
nix fmt
nix flake check --all-systems --no-build
git diff -- flake.nix flake.lock
```

Review package, service, and lockfile changes before committing. Existing
warnings about the custom `systemConfigs` flake output and unavailable foreign
build systems must be recorded, not silently ignored; no activation should rely
on a warning being harmless.

## Troubleshooting

| Symptom                                        | Safe response                                                                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Existing file blocks Home Manager              | Inspect it with `hm-preflight`, then use `hm-switch` so any collision is recorded in the manifest.                     |
| Cloudtop resolves `/nonexistent/cloudtop-home` | You omitted `--impure`, or `$HOME` is unset. Stop and fix the invoking account/environment.                            |
| `sops` cannot decrypt Lenovo secrets           | Confirm the identity path, permissions, recipient in `.sops.yaml`, and encrypted file before switching.                |
| A package collision occurs                     | Do not force activation. Remove the duplicate ownership intentionally; pacman/Nix overlap is not an automatic handoff. |
| Aslan validation fails                         | Do not retire the legacy hook. Restore from the root backup and investigate before another switch.                     |
| A Nix command lacks flake support              | Enable `nix-command flakes` through the installer configuration or use the temporary experimental-features flag above. |
