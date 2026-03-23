-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here
-- Autocommands (https://neovim.io/doc/user/autocmd.html)
local Idgroup = vim.api.nvim_create_augroup("MyGroup", { clear = true })
vim.api.nvim_clear_autocmds({ group = "MyGroup" })
vim.api.nvim_create_autocmd("InsertEnter", {
  pattern = { "*" },
  command = "norm zz",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*" },
  command = "set guicursor=a:ver20",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*.tex" },
  command = "!rm indent.log",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("lsp_attach_disable_ruff_hover", { clear = true }),
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if client == nil then
      return
    end
    if client.name == "ruff" then
      -- Disable hover in favor of Pyright
      client.server_capabilities.hoverProvider = false
    end
  end,
  desc = "LSP: Disable hover capability from Ruff",
})
vim.api.nvim_create_autocmd("BufEnter", {
  pattern = { "*" },
  -- command = "set wrap list listchars=space:· linebreak"
  command = "set wrap nolist listchars=space:· linebreak",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("BufEnter", {
  pattern = { "*.md" },
  command = "set nowrap nolist nolinebreak",
  group = Idgroup,
})
vim.cmd([[
augroup filetypedetect
  au! BufRead,BufNewFile *.m set filetype=octave
augroup END
]])
vim.api.nvim_create_autocmd("Filetype", { pattern = "rust", command = "set colorcolumn=100", group = Idgroup })
vim.api.nvim_create_autocmd("Filetype", {
  pattern = { "rust", "python" },
  callback = function(ev)
    -- actual mapping
    vim.api.nvim_buf_set_keymap(0, "n", "u", "2u", { noremap = true, silent = true, desc = "hack for auto-save" })
  end,
  group = Idgroup,
})

local uv = vim.uv

vim.api.nvim_create_autocmd({ "VimEnter", "VimLeave" }, {
  callback = function()
    if vim.env.TMUX_PLUGIN_MANAGER_PATH then
      uv.spawn(vim.env.TMUX_PLUGIN_MANAGER_PATH .. "/tmux-window-name/scripts/rename_session_windows.py", {})
    end
  end,
})
