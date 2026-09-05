# dots

## What This Is

Personal dotfiles repository managed with [chezmoi](https://www.chezmoi.io/). Uses Go templates for machine-conditional configs and age encryption for secrets. A single branch supports five profiles: `lenovo`, `cloudtop`, `macbook`, `hp`, and `hetzner` (`aslan`).

## Installation

```bash
chezmoi init --source /path/to/this/repo   # prompts for machine profile + secrets
chezmoi apply
```

Secrets are age-encrypted. Place the age key at `~/.config/chezmoi/key.txt` before init.

## Repository Structure

- `dot_config/` — XDG config home (`$HOME/.config`), chezmoi source layout
- `bin/` — user scripts for `$HOME/bin` (prefixed `executable_`)
- `system/` — system-level configs (`/etc/`, `/usr/`), deployed via `run_after_system-deploy.sh.tmpl` (subtrees for `arch/` and `hetzner/` are conditionally applied; preview with `chezmoi-dry-apply` or `system-deploy.sh --dry-run`)
- `pkgs` — full list of installed packages
- `.chezmoi.toml.tmpl` — chezmoi config template (machine detection, secrets, age settings)
- `.chezmoiignore` — machine-conditional file exclusion
- `markdown/` — documentation (features, keybinds, arch install guide, directory tree)

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

Files ending in `.tmpl` are Go templates rendered by chezmoi. Template variables are defined in `.chezmoi.toml.tmpl` and include machine flags (`is_lenovo`, `has_wayland`) and secrets (`opensubtitles_api_key`, `tstruct_token`). Encrypted files use the `encrypted_` prefix.

## Conventions

- NEVER KILL TMUX SERVER UNLESS I APPROVE
- XDG Base Directory compliance throughout — most tools are configured to respect `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`, `$XDG_CACHE_HOME`
- Git commits are GPG-signed (SSH key) per `dot_config/git/config`
- Catppuccin Mocha is the color scheme used across tools (zsh syntax highlighting, Qtile themes, FZF)

## Known Issues / TODOs

- `dot_claude/settings.json.tmpl` drifts frequently: Claude Code rewrites
  `~/.claude/settings.json` in its own non-alphabetical key order whenever
  it modifies the file (e.g. changing model, toggling settings). The
  chezmoi source has alphabetically-sorted keys (enforced by pre-commit
  hook), so every Claude Code write causes a fresh diff. Consider either
  excluding this file from chezmoi management or accepting periodic
  `chezmoi apply` re-syncs.
