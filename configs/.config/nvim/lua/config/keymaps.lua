-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
vim.keymap.set("n", "-", "<CMD>Oil<CR>", { desc = "Open parent directory" })
vim.keymap.set({ "n", "i" }, "<C-a>", "ggVG", { desc = "Select all text" })
vim.keymap.set("n", "<leader>z", "<CMD>ZenMode<CR>", { desc = "Toggle Zen Mode" })
