# Nix operations runbook

This is the operational guide for the staged migration from chezmoi. It applies
only to the existing operating systems; it does **not** install NixOS or replace
pacman, Homebrew, the kernel, bootloader, networking, or service data.

Read this document before any activation. Home Manager, nix-darwin, and System
Manager refuse many unsafe changes, but an activation still changes the target
account or host.

## Current ownership

| Area                                                             | Current owner             | Notes                                                                               |
| ---------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------- |
| Shared CLI/developer packages                                    | Home Manager              | Explicit package baseline only; legacy `pkgs` is not imported.                      |
| Pi, Claude, Gemini, and shared agent instructions                | Home Manager              | Authentication, caches, sessions, and downloaded plugins remain runtime state.      |
| Lenovo Transmission                                              | Home Manager              | Only after the encrypted Lenovo secret is present.                                  |
| Aslan `/etc`, `/www`, and selected systemd files                 | System Manager output     | Do not activate until the Aslan checklist passes.                                   |
| Zsh, Git, SSH, tmux, Neovim, lf, Alacritty, and desktop dotfiles | chezmoi source material   | These remain transitional until a later Home Manager module owns each destination.  |
| Cloudtop account and home directory                              | Existing Cloudtop account | The profile reads the activating account's `$HOME`; it never assumes `/home/ervin`. |

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
2. Confirm flakes work before continuing:

   ```bash
   nix --version
   nix flake --help >/dev/null
   ```

   If flakes are not enabled persistently yet, use
   `--extra-experimental-features 'nix-command flakes'` on every Nix command
   until the installer configuration is corrected.

3. Clone this repository as the target user and enter it:

   ```bash
   git clone git@github.com:ervinpopescu/dots.git ~/src/dots
   cd ~/src/dots
   git switch migration/nix-home-manager
   git pull --ff-only
   ```

4. Before changing a host, create an external backup or snapshot of its home
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
The preferred response is to inspect that file, migrate any wanted settings,
and move it deliberately. For a carefully reviewed first switch on Linux, use a
unique backup suffix so that known collisions are renamed rather than silently
overwritten:

```bash
backup_suffix="hm-before-nix-$(date +%F)"
nix run github:nix-community/home-manager -- \
  switch --flake .#ervin@lenovo -b "$backup_suffix"
```

Use the appropriate output in place of `lenovo`. A colliding path becomes, for
example, `~/.claude/settings.json.hm-before-nix-2026-08-20`. Activation still
fails if that backup name already exists; choose another suffix rather than
removing a backup. Backups are not automatically restored by a generation
rollback.

Cloudtop must run the same operation as its intended account and include
`--impure`:

```bash
test -n "$HOME" && test -d "$HOME"
nix run github:nix-community/home-manager -- \
  switch --impure --flake .#ervin@cloudtop -b "$backup_suffix"
```

After each successful Linux activation, verify the managed commands and agent
files without changing authentication state:

```bash
command -v git zsh tmux nvim pi claude gemini
systemctl --user status --no-pager
```

Home Manager rollback applies the preceding Home Manager generation, not any
manual file backups:

```bash
nix run github:nix-community/home-manager -- generations
nix run github:nix-community/home-manager -- switch --rollback
```

## Apple Silicon MacBook activation and rollback

First build as above, inspect any reported file collisions, and manually back
up conflicting agent files before switching. nix-darwin-integrated Home Manager
does not use the standalone `-b` option in this repository.

```bash
sudo nix run nix-darwin/master#darwin-rebuild -- \
  switch --flake .#macbook-apple-silicon
```

After bootstrap:

```bash
sudo darwin-rebuild switch --flake .#macbook-apple-silicon
sudo darwin-rebuild --list-generations
sudo darwin-rebuild switch --rollback
```

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
transmission/rpc-password: replace-with-a-real-secret
```

After a successful Lenovo Home Manager switch, validate:

```bash
stat -c '%a %n' ~/.config/transmission-daemon/settings.json
systemctl --user restart transmission
systemctl --user status --no-pager transmission
```

The settings file must have mode `600`. Confirm Transmission is bound as
configured and that no Aslan Transmission service, Nginx proxy, or server
configuration is reintroduced.

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
| Existing file blocks Home Manager              | Inspect it first; move it deliberately or use a new `-b` suffix for the first Linux switch.                            |
| Cloudtop resolves `/nonexistent/cloudtop-home` | You omitted `--impure`, or `$HOME` is unset. Stop and fix the invoking account/environment.                            |
| `sops` cannot decrypt Lenovo secrets           | Confirm the identity path, permissions, recipient in `.sops.yaml`, and encrypted file before switching.                |
| A package collision occurs                     | Do not force activation. Remove the duplicate ownership intentionally; pacman/Nix overlap is not an automatic handoff. |
| Aslan validation fails                         | Do not retire the legacy hook. Restore from the root backup and investigate before another switch.                     |
| A Nix command lacks flake support              | Enable `nix-command flakes` through the installer configuration or use the temporary experimental-features flag above. |
