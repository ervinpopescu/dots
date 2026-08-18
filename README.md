# Home, sweet home

```text
       ██              ██
  ▄███▄██   ▄████▄   ███████   ▄▄█████▄
 ██▀  ▀██  ██▀  ▀██    ██      ██▄▄▄▄ ▀
 ██    ██  ██    ██    ██       ▀▀▀▀██▄
 ▀██▄▄███  ▀██▄▄██▀    ██▄▄▄   █▄▄▄▄▄██
   ▀▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀    ▀▀▀▀▀▀
```

Cross-platform dotfiles for five machine profiles: `lenovo`, `cloudtop`,
`macbook`, `hp`, and `hetzner` (the `aslan` server hostname).
Managed with [chezmoi](https://www.chezmoi.io/), secrets age-encrypted, single branch.

**Stack:** Qtile · Zsh · Neovim (LazyVim) · Alacritty · Catppuccin Mocha

---

## Install

```bash
# 1. Install dependencies
pacman -S chezmoi age

# 2. Place age key (from backup / password manager)
mkdir -p ~/.config/chezmoi
cp /path/to/key.txt ~/.config/chezmoi/key.txt

# 3. Initialize — prompts for machine profile and secrets on first run
chezmoi init --source /path/to/this/repo

# 4. Preview, then apply
chezmoi diff
chezmoi apply
```

System files under `system/` (e.g. `/etc/zsh/zshenv`) are deployed automatically
via a post-apply script with `sudo`. The `system/hetzner/` subtree is applied only
when the machine profile is `aslan`/`hetzner`; it contains the server's Nginx,
monitoring, security, and service overrides.

The former `archnet-cfg` repository remains useful for destructive Hetzner
installation, package bootstrap, and service-data migration. It must not also
deploy files managed by this repository.

---

## Docs

- [Features](./markdown/features.md) — configs, tools, machine-specific behaviour
- [Profiles](./markdown/profiles.md) — profile detection, capabilities, and exclusions
- [Keybindings](./markdown/keybinds.md) — Qtile key reference
- [Directory tree](./markdown/tree.md) — repo layout explained
- [Arch install guide](./markdown/archinstall.md)

---

## Machine Profiles

| Profile    | Hostname | Platform / session      | Battery | Cursor |
| ---------- | -------- | ----------------------- | ------- | ------ |
| `lenovo`   | lenovo   | Linux / Qtile Wayland   | yes     | 24px   |
| `cloudtop` | cloudtop | Linux / Qtile X11 HiDPI | no      | 48px   |
| `macbook`  | prompted | macOS / native desktop  | yes     | n/a    |
| `hp`       | hp       | Linux / Qtile X11       | yes     | 48px   |
| `hetzner`  | aslan    | Linux / headless server | no      | n/a    |

The profiles are auto-selected for the `lenovo`, `cloudtop`, `hp`, and `aslan`
hostnames. `macbook` and unknown hosts use the profile prompt during
`chezmoi init`. See [Profiles](./markdown/profiles.md) for all capability flags
and machine-specific behavior.

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
