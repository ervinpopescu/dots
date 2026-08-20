# Repository Structure

```text
dots/                              # Nix/Home Manager source directory
├── flake.nix                      # pinned Nix/Home Manager entrypoint
├── nix/                            # reusable Home Manager, Darwin, and System Manager modules
├── secrets/                        # sops-nix encrypted secrets and instructions
├── .chezmoi.toml.tmpl             # transitional legacy config (to be removed)
├── .chezmoiignore                 # transitional legacy exclusions
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
├── private_dot_config/             # Private, profile-specific user config
│   └── transmission-daemon/        # Lenovo settings (migrating to sops-nix)
│
├── system/                        # Transitional system sources and Aslan System Manager inputs
│   ├── arch/                      # Remaining Arch-only legacy system configuration
│   │   └── etc/                   # pacman.conf, reflector.conf
│   ├── etc/
│   │   └── zsh/zshenv             # Sets ZDOTDIR system-wide
│   ├── hetzner/                   # Aslan-only server configuration
│   │   ├── etc/                   # Nginx, security, monitoring, and systemd
│   │   └── www/                   # Nginx homepage and error pages
│   └── usr/lib/python3.11/        # Custom Python logging library
│
├── markdown/                      # Documentation
│   ├── features.md
│   ├── nix-migration.md            # Migration architecture and boundaries
│   ├── nix-operations.md           # Host activation and recovery runbook
│   ├── profiles.md                # Machine profile matrix and detection
│   ├── keybinds.md
│   ├── tree.md                    # This file
│   └── archinstall.md             # Arch Linux installation guide
│
└── pkgs                           # Transitional legacy package inventory
```
