# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal Neovim configuration built on [LazyVim](https://lazyvim.github.io/) (a Neovim distribution using lazy.nvim as its plugin manager). All configuration is written in Lua.

## Formatting

Lua files are formatted with **StyLua**: 2-space indentation, spaces (not tabs), 120 column width. Config is in `stylua.toml`.

## Architecture

**Entry point:** `init.lua` sets `maplocalleader = "\"` and loads `config.lazy`.

**Config layer** (`lua/config/`):

- `lazy.lua` — bootstraps lazy.nvim, imports LazyVim base plugins + `lazyvim.plugins.extras.lang.python`, then imports user plugins from `lua/plugins/`
- `options.lua` — vim options (leader = space, 2-space tabs, 80-col colorcolumn, system clipboard, rg as grepprg)
- `keymaps.lua` — custom keymaps: `-` for Oil file browser, `<leader>z` for Zen Mode
- `autocmds.lua` — auto-center on insert, restore cursor shape on exit, filetype detection (`.m` → octave), Ruff hover disabled in favor of Pyright, wrap/list settings, rust colorcolumn=100, double-undo hack for auto-save in rust/python

**Plugin specs** (`lua/plugins/`): each file returns a lazy.nvim plugin spec table.

- `colorscheme.lua` — Catppuccin theme
- `disabled.lua` — explicitly disables flash.nvim and neo-tree
- `conform.lua` — formatter config (stylua, shfmt, prettier, ruff_format, rustfmt, taplo, custom jqfmt)
- `lspconfig.lua` — LSP opts overriding LazyVim defaults; servers: lua_ls, pyright, ruff, matlab_ls, ty; inlay hints enabled, codelens disabled, LSP folding enabled
- `user.lua` — additional plugins: auto-save, lastplace, trim, zen-mode, vimtex (LaTeX), oil.nvim, nvim-surround, multicursor.nvim, nvim-colorizer, diffview, treesitter-context, Preview.nvim, codeium, vim-matlab (local plugin)

**LazyVim extras** (from `lazyvim.json`): codeium, nvim-cmp, outline, clangd, json, markdown, rust, toml, mini-animate

## Key Design Decisions

- **Oil replaces neo-tree** as the file browser (neo-tree is explicitly disabled)
- **flash.nvim is disabled** — standard search is used instead
- **Auto-save is active** with 1s debounce; the `u` → `2u` remap in rust/python compensates for auto-save creating extra undo states
- **Python LSP**: Pyright (type checking off, diagnostics ignored) + Ruff (formatting/linting only, hover disabled)
- **lspconfig.lua uses opts-only pattern** — no custom `config` function, lets LazyVim handle the config lifecycle
- **Local plugin**: `vim-matlab` loaded from `~/src/mine/projects/nvim/plugins/vim-matlab`
- Custom plugins load eagerly by default (`lazy = false` in lazy.nvim defaults)
