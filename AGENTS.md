# dots

## What This Is

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/). Go templates
provide machine-conditional configuration and age encryption protects secrets.
One branch supports five profiles: `lenovo`, `cloudtop`, `macbook`, `hp`, and
`hetzner` (`aslan`).

## Installation

```bash
chezmoi init --source /path/to/this/repo   # prompts for machine profile + secrets
chezmoi apply
```

Secrets are age-encrypted. Place the age key at
`~/.config/chezmoi/key.txt` before initialization.

## Repository Structure

- `dot_config/` - XDG config home (`$HOME/.config`) in chezmoi source layout
- `bin/` - user scripts for `$HOME/bin` (files prefixed `executable_`)
- `system/` - system configs for `/etc` and `/usr`, deployed by
  `run_after_system-deploy.sh.tmpl`; `arch/` and `hetzner/` subtrees are
  conditionally applied
- `dot_agents/` - shared global agent guidance
- `dot_pi/` - Pi configuration and private agent files
- `pkgs` - complete package list
- `.chezmoi.toml.tmpl` - machine detection, secrets, and age settings
- `.chezmoiignore` - machine-conditional file exclusions
- `markdown/` - feature, keybind, installation, and directory-tree documentation

Preview changes with `chezmoi-dry-apply` or
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

Files ending in `.tmpl` are Go templates rendered by chezmoi. Variables in
`.chezmoi.toml.tmpl` include machine flags (`is_lenovo`, `is_cloudtop`,
`is_macbook`, `is_hp`, `is_hetzner`, `is_server`, and `is_linux`) and secrets
(`opensubtitles_api_key`, `tstruct_token`, and `openweather_api_key`). The
`encrypted_` prefix marks age-encrypted files; `private_` marks source
directories deployed with mode 0700.

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
