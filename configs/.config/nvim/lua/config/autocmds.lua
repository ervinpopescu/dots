-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here
-- Autocommands (https://neovim.io/doc/user/autocmd.html)
Idgroup = vim.api.nvim_create_augroup("MyGroup", { clear = true })
vim.api.nvim_clear_autocmds({ group = "MyGroup" })
vim.api.nvim_create_autocmd("InsertEnter", {
  pattern = { "*" },
  command = "normal zz",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*" },
  command = "set guicursor=a:ver20",
  group = Idgroup,
})
-- vim.api.nvim_create_autocmd("VimLeave", {
--   pattern = { "*" },
--   command = 'printf "e[6 q"',
--   group = Idgroup,
-- })
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*" },
  command = "set guicursor=a:ver20",
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
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*.md" },
  command = "!pkill qt_html.py",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*.md" },
  command = "!qtile cmd-obj -o group -f setlayout -a monadwide",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimEnter", {
  pattern = { "*.md" },
  command = "MarkdownPreviewToggle",
  group = Idgroup,
})
vim.api.nvim_create_autocmd("VimLeave", {
  pattern = { "*.md" },
  command = "!clear",
  group = Idgroup,
})
-- vim.api.nvim_create_autocmd("BufEnter", {
--   pattern = "*",
--   command = "ColorizerAttachToBuffer",
--   group = Idgroup,
-- })
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
