# Home, sweet home

```text
       ██              ██
  ▄███▄██   ▄████▄   ███████   ▄▄█████▄
 ██▀  ▀██  ██▀  ▀██    ██      ██▄▄▄▄ ▀
 ██    ██  ██    ██    ██       ▀▀▀▀██▄
 ▀██▄▄███  ▀██▄▄██▀    ██▄▄▄   █▄▄▄▄▄██
   ▀▀▀ ▀▀    ▀▀▀▀       ▀▀▀▀    ▀▀▀▀▀▀
```

Arch Linux dotfiles for two machines — `lenovo` (Wayland) and `cloudtop` (X11/HiDPI).
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
via a post-apply script with `sudo`.

---

## Docs

- [Features](./markdown/features.md) — configs, tools, machine-specific behaviour
- [Keybindings](./markdown/keybinds.md) — Qtile key reference
- [Directory tree](./markdown/tree.md) — repo layout explained
- [Arch install guide](./markdown/archinstall.md)

---

## Machine Profiles

| Profile    | Hostname | Display     | Battery | Cursor |
| ---------- | -------- | ----------- | ------- | ------ |
| `lenovo`   | lenovo   | Wayland     | yes     | 24px   |
| `cloudtop` | cloudtop | X11 (HiDPI) | no      | 48px   |

Templates use `{{ if .is_lenovo }}` / `{{ if .is_cloudtop }}` guards.
Machine is auto-detected from hostname; new machines are prompted on first `chezmoi init`.

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
