## Features

1. apps [config](/configs/.config)
   - **_global_**
     - [catppuccin](https://github.com/catppuccin) colorscheme
   - **_alacritty_** (mostly default, fonts and cursor changed)
   - **_conky_**
     - ~~_stolen_~~
     - \+ fortune cookie
   - **_neovim_**
     - mostly default [LazyVim](https://www.lazyvim.org)
     - added the following plugins:
       - `Pocco81/auto-save.nvim`
       - `norcalli/nvim-colorizer.lua`
       - `ethanholz/nvim-lastplace`
       - `iamcco/markdown-preview.nvim`
       - `prettier/vim-prettier`
       - **_check [/configs/.config/nvim/lua/plugins/user.lua](/configs/.config/nvim/lua/plugins/user.lua)_** for more plugins
   - **_nwg-launchers_**
     - nwgbar
       - used for powermenu
     - nwgdmenu
       - not used
     - nwggrid
       - rarely used
   - **_qtile_**:
     - Apps tied to specific groups
     - Mouse bindings for every widget
     - [Keybindings](./keybinds.md) for **_every freakin' program_**
     - Layouts that just **_make sense_**
     - Sensible picom config
   - **_reflector_**: the best config for my location and capabilities
   - **_rofi_**:
     - run, drun, window list
   - **_zathura_**:
     - clean af UI
   - **_zsh_**:
     - ~~**stolen**~~ from Kali Linux and added some stuff over time:
       - .zshenv:
         - env vars for $HOME cleaning
         - nvidia env vars (fuck nvidia)
         - random env vars
         - aliases
         - cleanup some systemd mess
       - .zshrc:
         - setopts that **_just make sense_**
         - keybindings, completions, prompt

2. 79 scripts that each do one thing only
   (KISS UNIX philosophy): [bin](/configs/bin/)
