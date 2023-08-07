return {
  "jose-elias-alvarez/null-ls.nvim",
  opts = function(_, config)
    -- config variable is the default configuration table for the setup function call
    local null_ls = require "null-ls"

    -- Check supported formatters and linters
    -- https://github.com/jose-elias-alvarez/null-ls.nvim/tree/main/lua/null-ls/builtins/formatting
    -- https://github.com/jose-elias-alvarez/null-ls.nvim/tree/main/lua/null-ls/builtins/diagnostics
    config.sources = {
      --lua
      null_ls.builtins.formatting.stylua,
      -- python
      null_ls.builtins.formatting.black,
      null_ls.builtins.formatting.isort,
      -- latex
      null_ls.builtins.formatting.latexindent,
      null_ls.builtins.diagnostics.chktex,
    }
    return config -- return final config table
  end,
}
