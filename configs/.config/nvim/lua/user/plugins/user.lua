return {
  {
    "folke/todo-comments.nvim",
    event = "User AstroFile",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function() require("todo-comments").setup {} end,
  },
  {
    "Pocco81/auto-save.nvim",
    config = function() require("auto-save").setup { debounce_delay = 1000 } end,
    lazy = false,
  },
  {
    "ethanholz/nvim-lastplace",
    event = "BufRead",
    config = function()
      require("nvim-lastplace").setup {
        lastplace_ignore_buftype = { "quickfix", "nofile", "help" },
        lastplace_ignore_filetype = {
          "gitcommit",
          "gitrebase",
          "svn",
          "hgcommit",
        },
        lastplace_open_folds = true,
      }
    end,
  },
  {
    "iamcco/markdown-preview.nvim",
    ft = "markdown",
    build = function() vim.fn["mkdp#util#install"]() end,
    config = function()
      vim.g.mkdp_auto_start = 1
      vim.g.mkdp_auto_close = 0
      vim.g.mkdp_echo_preview_url = 1
      vim.g.mkdp_browser = "/home/ervin/bin/md-preview.py"
      vim.g.mkdp_markdown_css = "/home/ervin/.config/md-preview/markdown.css"
      vim.g.mkdp_port = "8555"
      vim.g.mkdp_open_to_the_world = 0
      vim.g.mkdp_theme = "dark"
    end,
    lazy = false,
  },
  {
    "cappyzawa/trim.nvim",
    config = function()
      require("trim").setup {
        -- if you want to ignore markdown file.
        -- you can specify filetypes.
        ft_blocklist = { "markdown" },
        -- if you want to ignore space of top
        patterns = {
          [[%s/\s\+$//e]],
          [[%s/\($\n\s*\)\+\%$//]],
          [[%s/\(\n\n\)\n\+/\1/]],
        },
      }
    end,
    lazy = false,
  },
  {
    "folke/zen-mode.nvim",
    config = function() require("zen-mode").setup {} end,
    lazy = false,
  },
  {
    "lervag/vimtex",
    dependencies = { "L3MON4D3/LuaSnip", "sirver/ultisnips", "KeitaNakamura/tex-conceal.vim" },
    config = function()
      vim.g.tex_flavor = "xelatex"
      vim.g.vimtex_view_method = "zathura"
      vim.g.vimtex_compiler_silent = true
      vim.g.vimtex_quickfix_mode = 0
      vim.g.tex_conceal = "abdmg"
      vim.cmd [[
      let g:vimtex_syntax_conceal = {
          \ 'accents': 1,
          \ 'ligatures': 1,
          \ 'cites': 1,
          \ 'fancy': 1,
          \ 'spacing': 1,
          \ 'greek': 1,
          \ 'math_bounds': 1,
          \ 'math_delimiters': 1,
          \ 'math_fracs': 1,
          \ 'math_super_sub': 1,
          \ 'math_symbols': 1,
          \ 'sections': 1,
          \ 'styles': 1,
          \}
      ]]
      vim.cmd "set conceallevel=2"
      vim.cmd 'let maplocalleader = ","'
    end,
    lazy = false,
  },
  {
    "L3MON4D3/LuaSnip",
    config = function()
      require("luasnip.loaders.from_lua").load { paths = "~/.config/nvim/LuaSnip/" }
      require("luasnip.loaders.from_vscode").lazy_load()
    end,
    lazy = false,
  },
  { "shaunsingh/nord.nvim" },
  {
    "sirver/ultisnips",
    config = function()
      vim.cmd [[
        let g:UltiSnipsExpandTrigger = '<tab>'
        let g:UltiSnipsJumpForwardTrigger = '<tab>'
        let g:UltiSnipsJumpBackwardTrigger = '<s-tab>'
        let g:UltiSnipsSnippetDirectories=[$HOME.'/.config/nvim/UltiSnips']
      ]]
    end,
    lazy = false,
  },
  {
    "KeitaNakamura/tex-conceal.vim",
    config = function()
      vim.cmd [[
        hi Conceal ctermbg=none
      ]]
    end,
    lazy = false,
  },
  {
    "https://gitlab.com/somini/vim-octave.vim",
    ft = "octave",
  },
  {
    "stevearc/oil.nvim",
    config = function()
      require("oil").setup {
        columns = {
          "icon",
          "permissions",
          "size",
          "mtime",
        },
        view_options = { show_hidden = true },
      }
    end,
  },
  { "mg979/vim-visual-multi" },
}
