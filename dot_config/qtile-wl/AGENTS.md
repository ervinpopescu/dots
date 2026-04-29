# Qtile Wayland Config

## What This Is

A modular Qtile window manager configuration for Wayland. The entry point is `config.py`, which imports all modules and exposes the variables Qtile expects (keys, groups, layouts, screens, mouse, widget_defaults, etc.).

## Applying Changes

Qtile reads this config at startup and on manual reload. To apply changes:

```bash
# Reload config (from within Qtile)
# Default keybind: mod4 + ctrl + r

# Restart Qtile (full restart, re-reads everything)
# Default keybind: mod4 + ctrl + q (then relaunch)

# Check config for errors before reloading
qtile cmd-obj -o cmd -f reload_config
```

## Code Style

Enforced via `pyproject.toml`:

- **Black** with `line-length = 98`
- **isort** with `profile = "black"`

```bash
black .
isort .
```

## Architecture

### Configuration flow

```text
config.py
  └── modules/__init__.py  (re-exports all submodules)
       ├── settings.py      (loads json/settings.json + json/config.json, theme)
       ├── keys/            (keybindings split by category)
       ├── groups/          (workspace groups + scratchpad)
       ├── layouts.py       (layout list)
       ├── screens.py       (bar + widget configuration)
       ├── hooks/           (autostart, window rules, misc events)
       ├── mouse.py
       ├── matches.py       (app→group assignment)
       ├── decorations.py   (qtile_extras RectDecoration helpers)
       ├── functions.py     (lazy functions for window/group management)
       └── idle_timers.py   (DPMS / suspend)
```

### JSON-driven settings

User-facing configuration lives in `json/` — edit these instead of Python when possible:

| File                     | Purpose                                                              |
| ------------------------ | -------------------------------------------------------------------- |
| `json/settings.json`     | Bar height, fonts, margins, group definitions, commands, keymaps     |
| `json/config.json`       | Qtile global flags (follow_mouse_focus, cursor_warp, theme, xcursor) |
| `json/window_rules.json` | Per-app floating rules, sizes, positions                             |
| `json/matches.json`      | App class → workspace group mapping                                  |
| `json/themes.json`       | Available theme names                                                |

`json/config.json` is loaded by `config.py` at startup, so every key becomes a top-level Qtile variable.

### Themes

Themes are in `themes/catppuccin.json` and `themes/nord.json`. The active theme is set via `"theme"` in `json/config.json` and loaded in `modules/theme.py`. Colors are accessed throughout via the loaded theme dict.

### Widgets

Custom widgets live in `widgets/` (thin wrappers) and `extras/widgets/` (heavier implementations). Standard `libqtile.widget` and `qtile_extras` widgets are also used. The bar layout is defined in `modules/screens.py`.

### Groups (workspaces)

Six named groups defined in `json/settings.json`: `www`, `coding`, `media`, `settings`, `etc`, `social`. Each has a `screen_affinity` (0, 1, or 2) and a default layout. The `groups/scratchpad.py` module provides mutable scratchpad support via `extras/mutablescratch.py`.

### Key bindings

Split across `keys/`:

- `apps.py` — launchers, scratchpad dropdowns, KeyChord submenus
- `windows_and_groups.py` — workspace navigation
- `layouts.py` / `layout_managing.py` / `window_managing.py` — layout control
- `qtile_stuff.py` — reload, color scheme change
- `de.py` — desktop environment (volume, brightness, screenshots, lock)

`mod` key is `mod4` (Super); `alt` is `mod1`.

### Hooks

`hooks/apps.py` — runs `~/.config/qtile-wl/scripts/` autostart on startup/shutdown.
`hooks/window_rules.py` — assigns windows to groups and sets floating state on `client_new`.
`hooks/misc.py` — wallpaper changes on screen reconfiguration, urgency hints.

## Key Dependencies

- `libqtile` — core WM
- `qtile_extras` — additional widgets and `RectDecoration`
- `psutil` — system stats widgets
- `notify2` — desktop notifications
- `json5` — JSON5 parsing for flexible config files
- `jsonpickle` — group state serialization (group state persistence across restarts)
- `rofi` — launcher menus
