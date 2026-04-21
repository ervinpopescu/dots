# Repository Structure

```text
dots/                              # chezmoi source directory
├── .chezmoi.toml.tmpl             # per-machine config (machine detection, secrets, age)
├── .chezmoiignore                 # machine-conditional file exclusions
├── .pre-commit-config.yaml        # code quality hooks (black, isort, ruff, stylua, shellcheck…)
│
├── bin/                           # → $HOME/bin (user scripts)
│   ├── *.py                       # Python utilities (wallpaper, theme, bt-bat, pop-report…)
│   ├── *.sh                       # Shell utilities (run_wall, filesizes, git-status…)
│   └── *.tmpl                     # Templated scripts (wallpaper.sh, wallpaper-wl.sh)
│
├── dot_config/                    # → $HOME/.config
│   ├── alacritty/                 # Terminal emulator
│   ├── conky/                     # System monitor (Lua config)
│   ├── dunst/                     # Notification daemon
│   ├── git/                       # Git config (config.tmpl — cloudtop-conditional includeIf)
│   ├── lazygit/                   # TUI git client
│   ├── lf/                        # Terminal file manager
│   ├── md-preview/                # Markdown preview CSS
│   ├── nvim/                      # Neovim (LazyVim-based)
│   │   └── lua/plugins/
│   │       └── lspconfig.lua.tmpl # LSP config (lemminx/Apigee only on cloudtop)
│   ├── nwg-launchers/             # nwgbar (powermenu), nwgdmenu, nwggrid
│   ├── picom.conf.tmpl            # Compositor (xrender backend on cloudtop)
│   ├── qtile/                     # Qtile X11 window manager
│   │   ├── modules/               # Python modules (keys, groups, layouts, screens, hooks…)
│   │   ├── extras/widgets/        # Custom widget implementations
│   │   ├── json/                  # JSON-driven settings (settings, config, rules, matches)
│   │   └── themes/                # catppuccin.json, nord.json
│   ├── qtile-wl/                  # Qtile Wayland window manager
│   │   ├── modules/               # Same structure as qtile/
│   │   ├── extras/widgets/
│   │   ├── json/
│   │   └── themes/
│   ├── rofi/                      # App launcher themes
│   ├── spicetify/                 # Spotify client extensions
│   ├── tmux/                      # Terminal multiplexer
│   ├── VSCodium/                  # VSCodium settings (JSONC)
│   ├── X11/
│   │   └── Xresources.tmpl        # X resources (cursor size: 24 on lenovo, 48 on cloudtop)
│   ├── zathura/                   # PDF viewer
│   └── zsh/                       # Zsh config (ZDOTDIR=$XDG_CONFIG_HOME/zsh)
│       ├── env/                   # Variables, aliases, functions, path
│       ├── rc/                    # Keys, opts, completions, prompt, hooks
│       ├── plugins/               # Zsh plugins
│       └── files/                 # Misc zsh files
│
├── system/                        # System-level configs, deployed via run_after_ script
│   ├── etc/
│   │   ├── xdg/                   # XDG defaults
│   │   └── zsh/zshenv             # Sets ZDOTDIR system-wide
│   └── usr/lib/python3.11/        # Custom Python logging library
│
├── markdown/                      # Documentation
│   ├── features.md
│   ├── keybinds.md
│   ├── tree.md                    # This file
│   └── archinstall.md             # Arch Linux installation guide
│
└── pkgs                           # Full list of installed packages
```
