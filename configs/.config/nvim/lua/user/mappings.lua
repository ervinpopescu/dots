-- Mapping data with "desc" stored directly by vim.keymap.set{}.
--
-- Please use this mappings table to set keyboard mapping since this is the
-- lower level configuration and more robust one. {which-key will
-- automatically pick-up stored data by this setting.}
return {
  -- first key is the mode
  n = {
    ["<leader>b"] = { name = "Buffers" },
    ["<leader>bn"] = { "<cmd>tabnew<cr>", desc = "New tab" },
    ["<leader>bD"] = {
      function()
        require("astronvim.utils.status").heirline.buffer_picker(
          function(bufnr) require("astronvim.utils.buffer").close(bufnr) end
        )
      end,
      desc = "Pick to close",
    },
    ["-"] = { require("oil").open, desc = "Open parent directory" },
    ["<C-d>"] = { "<C-d>zz" },
    ["<C-s>"] = { ":w!<cr>", desc = "Save File" },
    ["<C-u>"] = { "<C-u>zz" },
    ["<leader>x"] = { "<cmd>!chmod +x %<CR>", silent = true },
    ["<leader>y"] = { [["+y]] },
    ["J"] = { "mzJ`z" },
    ["N"] = { "Nzzzv" },
    ["n"] = { "nzzzv" },
    ["Q"] = { "<nop>" },
    ["<leader><leader>"] = { function() vim.cmd "so" end },
  },
  i = {
    ["<C-c>"] = { "<Esc>" },
  },
  v = {
    ["<leader>Y"] = { [["+Y]] },
    ["<leader>y"] = { [["+y]] },
    ["J"] = { ":m '>+1<CR>gv=gv" },
    ["K"] = { ":m '<-2<CR>gv=gv" },
  },
  x = { ["<leader>p"] = { [["_dP]] } },
  t = {
    -- setting a mapping to false will disable it
    -- ["<esc>"] = false,
  },
}
