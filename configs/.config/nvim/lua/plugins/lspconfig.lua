return {
  "neovim/nvim-lspconfig",
  opts = {
    inlay_hints = {
      enabled = true,
      exclude = { "vue" },
    },
    codelens = {
      enabled = false,
    },
    folds = {
      enabled = true,
    },
    servers = {
      stylua = { enabled = false },
      lua_ls = {
        settings = {
          Lua = {
            workspace = {
              checkThirdParty = false,
            },
            codeLens = {
              enable = true,
            },
            completion = {
              callSnippet = "Replace",
            },
            doc = {
              privateName = { "^_" },
            },
            hint = {
              enable = true,
              setType = false,
              paramType = true,
              paramName = "Disable",
              semicolon = "Disable",
              arrayIndex = "Disable",
            },
          },
        },
      },
      matlab_ls = {
        settings = {
          MATLAB = {
            indexWorkspace = true,
            installPath = os.getenv("HOME") .. "/matlab/R2024a",
            telemetry = false,
            lint = {
              enable = true,
              reportProgress = true,
              reportUnusedVariable = "all",
            },
          },
        },
        single_file_support = true,
      },
    },
    setup = {
      ty = function(_, opts)
        require("lspconfig").ty.setup({
          settings = {
            ty = {},
          },
        })
      end,
      pyright = function()
        local utils = require("lspconfig/util")
        local capabilities = require("cmp_nvim_lsp").default_capabilities()
        require("lspconfig").pyright.setup({
          capabilities = capabilities,
          root_dir = utils.root_pattern({
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
            "pyrightconfig.json",
          }) or vim.uv.cwd(),
          settings = {
            pyright = {
              disableOrganizeImports = false,
            },
            python = {
              analysis = {
                autoSearchPaths = true,
                useLibraryCodeForTypes = true,
                diagnosticMode = "workspace",
                disableOrganizeImports = false,
                pythonPlatform = "Linux",
                extraPaths = { "./src" },
                ignore = { "*" },
                typeCheckingMode = "off",
              },
            },
          },
          filetypes = { "python" },
        })
      end,
      ruff = function()
        require("lspconfig").ruff.setup({
          init_option = {
            settings = {
              loglevel = "error",
            },
          },
          filetypes = { "python" },
        })
      end,
    },
  },
}
