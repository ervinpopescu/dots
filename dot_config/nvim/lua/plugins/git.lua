return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewFileHistory" },
  },
  {
    "romek-codes/lazygit.nvim",
    branch = "feat/lazygit-worktree-switch",
    lazy = true,
    cmd = {
      "LazyGit",
      "LazyGitConfig",
      "LazyGitCurrentFile",
      "LazyGitFilter",
      "LazyGitFilterCurrentFile",
    },
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    init = function()
      vim.g.lazygit_worktree_switch = 1
    end,
    keys = {
      { "<leader>gg", "<cmd>LazyGit<cr>", desc = "LazyGit" },
      { "<leader>gG", "<cmd>LazyGitCurrentFile<cr>", desc = "LazyGit (Current File)" },
    },
  },
}
