# dots

## What This Is

Cross-platform configuration repository managed by a pinned Nix flake. Home Manager owns user configuration and development tools, nix-darwin integrates macOS, and System Manager owns migrated Aslan runtime files. Active outputs support `lenovo`, `cloudtop`, `macbook`, `hp`, and `aslan`. Cloudtop uses the invoking account's existing `$HOME` under impure evaluation and must never assume or create `/home/ervin`.

## Installation

See `markdown/nix-migration.md` and `markdown/nix-operations.md`. The primary
entrypoint is `flake.nix`; Linux hosts use standalone Home Manager, macOS uses
nix-darwin, and Aslan system files use System Manager. Encrypted secrets use
sops-nix.

## Repository Structure

- `nix/` — Home Manager, nix-darwin, System Manager, and profile modules
- `dot_config/` — transitional source material for user configuration
- `bin/` — user scripts for `$HOME/bin` (prefixed `executable_`)
- `system/` — transitional system source material; `arch/` remains legacy-host scoped while `hetzner/` feeds the Aslan System Manager configuration
- `secrets/` — sops-nix encrypted secrets and instructions
- `flake.nix` — pinned multi-host entrypoint
- `pkgs` — transitional legacy package inventory
- `.chezmoi.toml.tmpl` — transitional chezmoi config template
- `.chezmoiignore` — transitional machine-conditional exclusions
- `markdown/` — documentation (features, profiles, migration, operations, keybinds, tree)

## Key Configurations

### Zsh (`dot_config/zsh/`)

Entrypoint chain: `.zshenv` → sources `env/*.zsh` (vars, aliases, functions, bookmarks, path). `.zshrc` → sources plugins then `rc/*.zsh` modules (keys, opts, completions, prompt, hooks). `.zprofile` → auto-starts X (tty2) or Qtile Wayland (tty3).

`ZDOTDIR` is set to `$XDG_CONFIG_HOME/zsh` (via `/etc/zsh/zshenv`), not `$HOME`.

### Qtile Wayland (`dot_config/qtile-wl/`)

See `dot_config/qtile-wl/AGENTS.md` for detailed architecture. Entry point: `config.py`. Modular Python config with JSON-driven settings in `json/`. Formatting: Black (line-length 98) + isort (profile "black").

### Tmux (`dot_config/tmux/`)

Single config file: `tmux.conf`.

### Neovim (`dot_config/nvim/`)

LazyVim-based configuration. Entry point: `init.lua`. Lua config in `lua/`. Formatting enforced by `stylua.toml`.

## Templating

New machine conditionals belong in Nix profile modules under `nix/`; do not add
new Go templates or chezmoi-only flags. Existing `.tmpl` files are transitional
source material and are removed as their destinations move to Home Manager.

## Conventions

- NEVER KILL TMUX SERVER UNLESS I APPROVE
- XDG Base Directory compliance throughout — most tools are configured to respect `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`, `$XDG_CACHE_HOME`
- Git commits are GPG-signed (SSH key) per `dot_config/git/config`
- Catppuccin Mocha is the color scheme used across tools (zsh syntax highlighting, Qtile themes, FZF)

## Known Issues / TODOs

- The Nix migration is staged. Do not delete the remaining chezmoi source
  material until each Home Manager destination has been activated and verified.
- `flake.lock` must be generated and committed from a host with Nix installed;
  the current development environment does not provide the Nix CLI.
