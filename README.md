# Home, sweet home

```text
       ██              ██
  ▄███▄██   ▄████▄   ███████   ▄▄█████▄
 ██▀  ▀██  ██▀  ▀██    ██      ██▄▄▄▄ ▀
 ██    ██  ██    ██    ██       ▀▀▀▀██▄
 ▀██▄▄███  ▀██▄▄██▀    ██▄▄▄   █▄▄▄▄▄██
   ▀▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀    ▀▀▀▀▀▀
```

Cross-platform configuration for five machine profiles: `lenovo`, `cloudtop`,
`macbook`, `hp`, and `aslan` (the legacy `hetzner` profile name). Cloudtop uses
the invoking account's existing `$HOME`; it does not assume `/home/ervin`.
Managed with Nix, Home Manager, nix-darwin, and System Manager in a single flake.

**Stack:** Qtile · Zsh · Neovim (LazyVim) · Alacritty · Catppuccin Mocha

---

## Install

Install Nix with flakes enabled, then lock and check the flake:

```bash
nix flake lock
nix flake check
```

During the staged migration, remaining legacy system sources retain their
existing host conditions: `system/arch/` is Arch-only, while active Aslan
runtime configuration from `system/hetzner/` is moving to System Manager.
Do not let the legacy post-apply hook and System Manager deploy the same path.
Web-serving Nginx configs and the static pages in `/www/data` live in the
private [archnet-cfg repository](https://github.com/ervinpopescu/archnet-cfg),
not here; that repository deploys them with its own `deploy.sh`. The fail2ban
Nginx jail stays under `system/hetzner/`.

On Linux, activate the matching standalone Home Manager profile:

```bash
nix run github:nix-community/home-manager -- \
  switch --flake .#ervin@lenovo
```

On macOS, use the matching nix-darwin architecture output:

```bash
darwin-rebuild switch --flake .#macbook-apple-silicon
```

The `system/hetzner/` subtree is exposed through `systemConfigs.aslan` for
System Manager. It owns active Aslan Nginx, monitoring, security, and systemd
runtime configuration without replacing the Linux distribution or its native
package manager. See the [Nix operations runbook](./markdown/nix-operations.md)
before activating it.

While legacy chezmoi sources remain during the migration, they can be
previewed with the wrappers below.

To preview pending legacy changes safely without mutating `/etc`, modifying files, or
reloading services, run:

```bash
chezmoi-dry-apply
```

This single command previews both normal chezmoi user dotfile changes
(`chezmoi apply --dry-run --verbose`) and system configuration changes.

> **Warning:** Running `chezmoi apply --dry-run` or `chezmoi diff` alone
> **skips post-apply lifecycle hooks** (`run_after_system-deploy.sh.tmpl`).
> Running `chezmoi apply --dry-run` will therefore never preview system files
> under `/etc` or `/usr`. Always use `chezmoi-dry-apply` to safely inspect both
> user dotfiles and system changes together.

To preview system configuration changes alone, run:

```bash
system-deploy.sh --dry-run   # or: system-deploy.sh -n
```

Key dry-run safety features:

- **Worktree Source Detection:** When invoked from inside a git feature worktree,
  both `chezmoi-dry-apply` and `system-deploy.sh` automatically detect and use that
  worktree's source templates instead of falling back to the main configured chezmoi
  source path.
- **Fail-Closed Protection:** If `--dry-run` is requested but the target template
  lacks explicit dry-run capability headers (`SYSTEM_DEPLOY_CAPABILITIES`), execution
  aborts immediately with an error to prevent accidental live mutation.
- **Guarded Destructive Cleanup:** Decommissioned configurations and service removals
  are reported as `[dry-run] would remove ...` without deleting any files. Setting
  `DRY_RUN=1` in the environment also activates dry-run mode.

`archnet-cfg` remains responsible for destructive installation, bootstrap,
disk/data migration, and service-data migration. It must not deploy runtime
paths owned by this repository.

---

## Docs

- [Features](./markdown/features.md) — configs, tools, machine-specific behaviour
- [Profiles](./markdown/profiles.md) — profile detection, capabilities, and exclusions
- [Keybindings](./markdown/keybinds.md) — Qtile key reference
- [Directory tree](./markdown/tree.md) — repo layout explained
- [Nix migration](./markdown/nix-migration.md) — architecture and migration boundary
- [Nix operations](./markdown/nix-operations.md) — host preflight, activation, validation, and recovery
- [Arch install guide](./markdown/archinstall.md)

---

## Machine Profiles

| Profile    | Hostname | Platform / session      | Battery | Cursor |
| ---------- | -------- | ----------------------- | ------- | ------ |
| `lenovo`   | lenovo   | Linux / Qtile Wayland   | yes     | 24px   |
| `cloudtop` | cloudtop | Linux / Qtile X11 HiDPI | no      | 48px   |
| `macbook`  | prompted | macOS / native desktop  | yes     | n/a    |
| `hp`       | hp       | Linux / Qtile X11       | yes     | 48px   |
| `aslan`    | aslan    | Linux / headless server | no      | n/a    |

Flake outputs select the active profiles explicitly. Linux keeps its current
system distribution; macOS uses nix-darwin. Cloudtop must be activated with
`--impure` so it uses the invoking account's `$HOME`. See
[Profiles](./markdown/profiles.md) for all capability flags and [Nix
migration](./markdown/nix-migration.md) for activation commands.

---

## Code Quality

Pre-commit hooks run on every commit:

| Hook               | Covers                                 |
| ------------------ | -------------------------------------- |
| black + isort      | Python (`bin/`, `qtile/`, `qtile-wl/`) |
| ruff               | Python linting + auto-fix              |
| stylua             | Lua (`nvim/`)                          |
| prettier           | JSON, YAML, CSS, Markdown              |
| shellcheck + shfmt | Shell scripts (`bin/`)                 |
| gitleaks           | Secret detection                       |

```bash
pre-commit install        # install hooks
pre-commit run --all-files  # run manually
```
