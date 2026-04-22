return {
  {
    "folke/noice.nvim",
    opts = {
      presets = { lsp_doc_border = true },
    },
  },
  {
    "catgoose/nvim-colorizer.lua",
    name = "nvim-colorizer",
    event = "VeryLazy",
    opts = {},
  },
  { "folke/twilight.nvim" },
  {
    "folke/todo-comments.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
      require("todo-comments").setup({})
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter-context",
    event = "VeryLazy",
    opts = { max_lines = 3 },
  },
  {
    "folke/zen-mode.nvim",
    lazy = false,
    config = function()
      require("zen-mode").setup({
        window = {
          backdrop = 0.95,
          width = 120,
          height = 1,
          options = {},
        },
        plugins = {
          options = { enabled = true, ruler = false, showcmd = false, laststatus = 0 },
          twilight = { enabled = true },
          gitsigns = { enabled = false },
          tmux = { enabled = true },
        },
        on_open = function(_) end,
        on_close = function() end,
      })
    end,
  },
  {
    "henriklovhaug/Preview.nvim",
    cmd = { "Preview" },
    config = function()
      require("preview").setup()
    end,
  },
}
