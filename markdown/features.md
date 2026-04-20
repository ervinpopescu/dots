# Features

## Window Manager — Qtile

Two configs: `qtile/` (X11) and `qtile-wl/` (Wayland). Both share the same architecture:

- **Modular Python config** — keys, groups, layouts, screens, hooks each in their own module
- **JSON-driven settings** — bar height, fonts, groups, keymaps, commands in `json/settings.json`; runtime flags in `json/config.json`
- **6 named workspaces** — `www`, `coding`, `media`, `settings`, `etc`, `social`, each with screen affinity
- **Custom widgets** — battery, BT battery, CPU temp, check-updates, tasklist, weather, uptime, widgetbox
- **Catppuccin Mocha** and Nord themes, runtime-switchable
- **Scratchpad** support with mutable scratchpads
- **Rofi** integration — app launcher, window switcher, wallpaper picker, layout switcher
- **Idle management** — DPMS / suspend via idle timers

## Shell — Zsh

- `ZDOTDIR=$XDG_CONFIG_HOME/zsh` (set system-wide via `/etc/zsh/zshenv`)
- `.zshenv` → `env/*.zsh` — path, aliases, functions, bookmarks, env vars
- `.zshrc` → plugins + `rc/*.zsh` — keybindings, setopts, completions, prompt, hooks
- `.zprofile` — auto-starts X on tty2 or Qtile Wayland on tty3
- Catppuccin syntax highlighting

## Editor — Neovim

- [LazyVim](https://www.lazyvim.org)-based config
- LSP via `lspconfig.lua.tmpl` — cloudtop gets lemminx (XML/XSD) for Apigee projects
- Plugins: auto-save, colorizer, lastplace, markdown-preview, prettier

## Terminal — Alacritty

- Catppuccin Mocha colors
- Custom keybindings (paste, copy, font size, new instance)

## Other Tools

| Tool              | Notes                                                   |
| ----------------- | ------------------------------------------------------- |
| **tmux**          | Single `tmux.conf`, battery plugin                      |
| **conky**         | Lua-based system monitor with fortune cookie            |
| **picom**         | Compositor — xrender backend on cloudtop, GLX elsewhere |
| **rofi**          | run / drun / window / emoji / wallpaper / layout menus  |
| **dunst**         | Notifications                                           |
| **nwg-launchers** | nwgbar powermenu                                        |
| **spicetify**     | Spotify client — Catppuccin Mocha + adblock extension   |
| **lazygit**       | TUI git client                                          |
| **lf**            | Terminal file manager                                   |
| **zathura**       | PDF viewer                                              |
| **VSCodium**      | Editor settings synced                                  |

## Scripts (`bin/`)

~70 user scripts covering:

- Wallpaper management (`wallpaper.sh`, `rofi-wallpaper`, `run_wall.sh`)
- Theme switching (`change_theme.py`)
- System info (`filesizes.sh`, `all_disk_usage.sh`, `bt-bat.py`, `location.py`)
- Media control (`volctl.sh`, `mutevol.sh`, `mediactl.sh`)
- Git helpers (`git-status`, `git-update-all`)
- Qtile helpers (`qtilekeys.py`, `update-qtile.py`, `switch_windows_in_group.py`)
- Misc utilities (`md-preview.py`, `pop-report.py`, `watcher.py`, `sort_json.py`)

## Machine Profiles

Managed via chezmoi templates. Two active profiles:

| Variable      | `lenovo`          | `cloudtop`           |
| ------------- | ----------------- | -------------------- |
| `has_wayland` | true              | false                |
| `has_battery` | true              | false                |
| Cursor size   | 24 (standard DPI) | 48 (HiDPI)           |
| picom backend | GLX               | xrender              |
| LSP extras    | —                 | lemminx (Apigee XSD) |
| Git includeIf | —                 | cgn project config   |
