# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Personal dotfiles repository for an Arch Linux setup. Configs are stored under `configs/` mirroring their target filesystem paths. The repo uses per-machine branches (`lenovo`, `cloudtop`) — the main branch is `lenovo`.

## Installation

Configs are deployed by hard-linking into place (not symlinked):
```bash
sudo cp -alf configs/etc/* /etc
cp -alf configs/.config/* $HOME/.config
cp -alf configs/bin/* $HOME/bin
```

After modifying any config file here, changes take effect immediately on the live system if the hard link is intact. Be aware of this — edits are not sandboxed.

## Repository Structure

- `configs/.config/` — XDG config home (`$HOME/.config`), contains the bulk of the dotfiles
- `configs/etc/` — system-level configs (`/etc/pacman.conf`, `/etc/zsh/`, `/etc/xdg/`)
- `configs/bin/` — user scripts for `$HOME/bin`
- `configs/usr/` — system library overrides
- `configs/pkgs` — full list of installed packages
- `markdown/` — documentation (features, keybinds, arch install guide, directory tree)

## Key Configurations

### Zsh (`configs/.config/zsh/`)

Entrypoint chain: `.zshenv` → sources `env/*.zsh` (vars, aliases, functions, bookmarks, path). `.zshrc` → sources plugins then `rc/*.zsh` modules (keys, opts, completions, prompt, hooks). `.zprofile` → auto-starts X (tty2) or Qtile Wayland (tty3).

`ZDOTDIR` is set to `$XDG_CONFIG_HOME/zsh` (via `/etc/zsh/zshenv`), not `$HOME`.

### Qtile Wayland (`configs/.config/qtile-wl/`)

See `configs/.config/qtile-wl/CLAUDE.md` for detailed architecture. Entry point: `config.py`. Modular Python config with JSON-driven settings in `json/`. Formatting: Black (line-length 98) + isort (profile "black").

### Tmux (`configs/.config/tmux/`)

Three config files: `tmux.conf` (shared), `tmux.conf.main` and `tmux.conf.mine` (machine-specific).

### Neovim (`configs/.config/nvim/`)

LazyVim-based configuration. Entry point: `init.lua`. Lua config in `lua/`. Formatting enforced by `stylua.toml`.

## Branch Strategy

Each machine gets its own branch. `lenovo` is the primary/default branch. Do not merge between machine branches — they diverge intentionally.

## Conventions

- XDG Base Directory compliance throughout — most tools are configured to respect `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`, `$XDG_CACHE_HOME`
- Git commits are GPG-signed (SSH key) per `configs/.config/git/config`
- Catppuccin Mocha is the color scheme used across tools (zsh syntax highlighting, Qtile themes, FZF)
