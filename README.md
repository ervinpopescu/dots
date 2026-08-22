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

On Linux, review and activate the matching standalone Home Manager profile with
the repository's pinned, manifest-backed commands:

```bash
nix run .#hm-preflight -- ervin@lenovo
nix run .#hm-switch -- ervin@lenovo
```

`hm-preflight` shows path-level changes without activation. Collision backups
are recorded as user state and restored automatically when rollback makes their
original paths unmanaged.

On macOS, use the matching nix-darwin architecture output:

```bash
darwin-rebuild switch --flake .#macbook-apple-silicon
```

The `system/hetzner/` subtree is exposed through `systemConfigs.aslan` for
System Manager. It owns active Aslan Nginx, monitoring, security, and systemd
runtime configuration without replacing the Linux distribution or its native
package manager. See the [Nix operations runbook](./markdown/nix-operations.md)
before activating it.

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

| Hook                      | Covers                                      |
| ------------------------- | ------------------------------------------- |
| black + isort             | Python (`bin/`, `qtile/`, `qtile-wl/`)      |
| ruff                      | Python linting + auto-fix                   |
| stylua                    | Lua (`nvim/`)                               |
| prettier                  | JSON, YAML, CSS, Markdown                   |
| shellcheck + shfmt        | Shell scripts, including `nix/scripts/`     |
| nixfmt + flake evaluation | Nix formatting and all-system output checks |
| Home Manager backup test  | Executable manifest backup/restore behavior |
| executable/shebang checks | Script mode and interpreter consistency     |
| gitleaks                  | Secret detection                            |

```bash
pre-commit install        # install hooks
pre-commit run --all-files  # run manually
```
