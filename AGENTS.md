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
- `dot_agents/` — shared global agent guidance
- `dot_pi/` — Pi configuration and private agent files
- `bin/` — user scripts for `$HOME/bin` (prefixed `executable_`)
- `system/` — transitional system source material; `arch/` remains legacy-host scoped while `hetzner/` feeds the Aslan System Manager configuration
- `secrets/` — sops-nix encrypted secrets and instructions
- `flake.nix` — pinned multi-host entrypoint
- `pkgs` — transitional legacy package inventory
- `.chezmoi.toml.tmpl` — transitional chezmoi config template
- `.chezmoiignore` — transitional machine-conditional exclusions
- `markdown/` — documentation (features, profiles, migration, operations, keybinds, tree)

Preview legacy chezmoi changes with `chezmoi-dry-apply` or
`system-deploy.sh --dry-run`. `chezmoi apply --dry-run` alone skips hooks, and
these wrappers detect the active worktree when run from one.

## Key Configurations

### Zsh (`dot_config/zsh/`)

The chain is `.zshenv` -> `env/*.zsh` (variables, aliases, functions,
bookmarks, and path), `.zshrc` -> plugins and `rc/*.zsh` modules (keys, options,
completions, prompt, and hooks), and `.zprofile` -> X on tty2 or Qtile Wayland
on tty3. `ZDOTDIR` is `$XDG_CONFIG_HOME/zsh`, set by `/etc/zsh/zshenv`, not
`$HOME`. Plugins use zplug, with `ZPLUG_HOME` selected by OS or machine.

### Qtile Wayland (`dot_config/qtile-wl/`)

See `dot_config/qtile-wl/AGENTS.md`. The entry point is `config.py`; the
configuration is modular Python with JSON-driven settings. Format with Black
(line length 98) and isort (profile `black`).

### Tmux (`dot_config/tmux/`)

Single configuration file: `tmux.conf`.

### Neovim (`dot_config/nvim/`)

LazyVim-based configuration. The entry point is `init.lua`, Lua configuration
lives under `lua/`, and formatting uses `stylua.toml`.

## Templating

New machine conditionals belong in Nix profile modules under `nix/`; do not add
new Go templates or chezmoi-only flags. Existing `.tmpl` files are transitional
source material and are removed as their destinations move to Home Manager.

## Conventions

- Do not kill the tmux server without approval.
- Keep non-main and feature branches in dedicated worktrees under
  `.worktrees/<branch-name>`; keep the primary checkout on `main`.
- Follow XDG Base Directory conventions.
- Git commits are GPG-signed with an SSH key, per `dot_config/git/config`.
- Use Catppuccin Mocha across tools, including zsh syntax highlighting, Qtile,
  and FZF.
- Pre-commit hooks run Black, ruff, shellcheck, shfmt, stylua, and jq key
  sorting.

## Known Issues / TODOs

- The Nix migration is staged. Do not delete the remaining chezmoi source
  material until each Home Manager destination has been activated and verified.
- `flake.lock` must be generated and committed from a host with Nix installed;
  the current development environment does not provide the Nix CLI.
