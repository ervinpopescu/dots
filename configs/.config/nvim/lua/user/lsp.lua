return {
  -- customize lsp formatting options
  formatting = {
    -- control auto formatting on save
    format_on_save = {
      enabled = true,     -- enable or disable format on save globally
      allow_filetypes = { -- enable format on save for specified filetypes only
        -- "go",
      },
      ignore_filetypes = { -- disable format on save for specified filetypes
        -- "python",
      },
    },
    disabled = { -- disable formatting capabilities for the listed language servers
      -- "sumneko_lua",
    },
    timeout_ms = 1000,        -- default format timeout
    filter = function(client) -- fully override the default formatting function
      if vim.bo.filetype ~= "markdown" then
        require("null-ls").disable({ "prettier" })
        return true
      end

      if vim.bo.filetype == "latex" then
        return client.name == "texlab"
      end

      return true
    end
  },
  -- enable servers that you already have installed without mason
  servers = {
    -- "pyright"
  },
}
