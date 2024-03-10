return {
  {
    "folke/todo-comments.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
      require("todo-comments").setup({})
    end,
  },
  {
    "Pocco81/auto-save.nvim",
    config = function()
      require("auto-save").setup({ debounce_delay = 1000 })
    end,
    lazy = false,
  },
  {
    "ethanholz/nvim-lastplace",
    event = "BufRead",
    config = function()
      require("nvim-lastplace").setup({
        lastplace_ignore_buftype = { "quickfix", "nofile", "help" },
        lastplace_ignore_filetype = {
          "gitcommit",
          "gitrebase",
          "svn",
          "hgcommit",
        },
        lastplace_open_folds = true,
      })
    end,
  },
  {
    "iamcco/markdown-preview.nvim",
    ft = "markdown",
    build = function()
      vim.fn["mkdp#util#install"]()
    end,
    config = function()
      vim.g.mkdp_auto_start = 0
      vim.g.mkdp_auto_close = 0
      vim.g.mkdp_echo_preview_url = 1
      vim.g.mkdp_browser = "/home/ervin/bin/md-preview.py"
      vim.g.mkdp_markdown_css = "/home/ervin/.config/md-preview/markdown.css"
      vim.g.mkdp_port = "8555"
      vim.g.mkdp_open_to_the_world = 0
      vim.g.mkdp_theme = "dark"
    end,
    lazy = true,
  },
  {
    "cappyzawa/trim.nvim",
    config = function()
      require("trim").setup({
        -- if you want to ignore markdown file.
        -- you can specify filetypes.
        ft_blocklist = { "markdown" },
        -- if you want to ignore space of top
        patterns = {
          [[%s/\s\+$//e]],
          [[%s/\($\n\s*\)\+\%$//]],
          [[%s/\(\n\n\)\n\+/\1/]],
        },
      })
    end,
    lazy = false,
  },
  {
    "folke/zen-mode.nvim",
    config = function()
      require("zen-mode").setup({
        window = {
          backdrop = 0.95, -- shade the backdrop of the Zen window. Set to 1 to keep the same as Normal
          -- height and width can be:
          -- * an absolute number of cells when > 1
          -- * a percentage of the width / height of the editor when <= 1
          -- * a function that returns the width or the height
          width = 120, -- width of the Zen window
          height = 1, -- height of the Zen window
          -- by default, no options are changed for the Zen window
          -- uncomment any of the options below, or add other vim.wo options you want to apply
          options = {
            -- signcolumn = "no", -- disable signcolumn
            -- number = false, -- disable number column
            -- relativenumber = false, -- disable relative numbers
            -- cursorline = false, -- disable cursorline
            -- cursorcolumn = false, -- disable cursor column
            -- foldcolumn = "0", -- disable fold column
            -- list = false, -- disable whitespace characters
          },
        },
        plugins = {
          -- disable some global vim options (vim.o...)
          -- comment the lines to not apply the options
          options = {
            enabled = true,
            ruler = false, -- disables the ruler text in the cmd line area
            showcmd = false, -- disables the command in the last line of the screen
            -- you may turn on/off statusline in zen mode by setting 'laststatus'
            -- statusline will be shown only if 'laststatus' == 3
            laststatus = 0, -- turn off the statusline in zen mode
          },
          twilight = { enabled = true }, -- enable to start Twilight when zen mode opens
          gitsigns = { enabled = false }, -- disables git signs
          tmux = { enabled = true }, -- disables the tmux statusline
        },
        -- callback where you can add custom code when the Zen window opens
        on_open = function(win) end,
        -- callback where you can add custom code when the Zen window closes
        on_close = function() end,
      })
    end,
    lazy = false,
  },
  -- {
  --   "lervag/vimtex",
  --   ft = "latex",
  --   dependencies = { "L3MON4D3/LuaSnip", "sirver/ultisnips", "KeitaNakamura/tex-conceal.vim" },
  --   config = function()
  --     vim.g.tex_flavor = "xelatex"
  --     vim.g.vimtex_view_method = "zathura"
  --     vim.g.vimtex_compiler_silent = true
  --     vim.g.vimtex_quickfix_mode = 0
  --     vim.g.tex_conceal = "abdmg"
  --     vim.cmd([[
  --     let g:vimtex_syntax_conceal = {
  --         \ 'accents': 1,
  --         \ 'ligatures': 1,
  --         \ 'cites': 1,
  --         \ 'fancy': 1,
  --         \ 'spacing': 1,
  --         \ 'greek': 1,
  --         \ 'math_bounds': 1,
  --         \ 'math_delimiters': 1,
  --         \ 'math_fracs': 1,
  --         \ 'math_super_sub': 1,
  --         \ 'math_symbols': 1,
  --         \ 'sections': 1,
  --         \ 'styles': 1,
  --         \}
  --     ]])
  --     vim.cmd("set conceallevel=2")
  --     vim.cmd('let maplocalleader = ","')
  --   end,
  --   lazy = true,
  -- },
  -- {
  --   "KeitaNakamura/tex-conceal.vim",
  --   config = function()
  --     vim.cmd([[
  --       hi Conceal ctermbg=none
  --     ]])
  --   end,
  --   lazy = false,
  -- },
  {
    "https://gitlab.com/somini/vim-octave.vim",
    ft = "octave",
  },
  {
    "stevearc/oil.nvim",
    config = function()
      require("oil").setup({
        columns = {
          "icon",
          "permissions",
          "size",
          "mtime",
        },
        view_options = { show_hidden = true },
      })
    end,
  },
  { "tpope/vim-surround" },
  { "norcalli/nvim-colorizer.lua" },
  { "folke/twilight.nvim" },
  { "shaunsingh/nord.nvim" },
}
