return {
  "neovim/nvim-lspconfig",
  opts = function(_, opts)
    -- Start of your custom lemminx logic
    local project_root = vim.fn.getcwd()
    local xsd_path = project_root .. "/xsd"
    local xsd_files = {}
    local xsd_dir_handle = vim.uv.fs_scandir(xsd_path)
    if xsd_dir_handle then
      while true do
        local name = vim.uv.fs_scandir_next(xsd_dir_handle)
        if not name then
          break
        end
        if name:match("%.xsd$") then
          table.insert(xsd_files, name)
        end
      end
    end

    local file_associations = {}
    if #xsd_files > 0 then
      for _, xsd_file in ipairs(xsd_files) do
        table.insert(file_associations, {
          systemId = xsd_path .. "/" .. xsd_file,
          pattern = project_root .. "/apiproxy/policies/*.xml",
        })
      end
      vim.notify("Apigee LSP: Loaded " .. #xsd_files .. " XSDs.", vim.log.levels.INFO)
    end
    -- End of custom lemminx logic

    -- Merge custom server configurations
    opts.servers = vim.tbl_deep_extend("force", opts.servers or {}, {
      stylua = { enabled = false },
      lemminx = {
        filetypes = { "xml" },
        settings = {
          xml = {
            schemas = file_associations,
            validation = { enabled = true },
          },
        },
      },
      lua_ls = {
        settings = {
          Lua = {
            workspace = { checkThirdParty = false },
            codeLens = { enable = true },
            completion = { callSnippet = "Replace" },
            doc = { privateName = { "^_" } },
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
    })

    -- Merge other options
    opts.inlay_hints = { enabled = true, exclude = { "vue" } }
    opts.codelens = { enabled = false }
    opts.folds = { enabled = true }

    -- Merge setup functions
    opts.setup = vim.tbl_deep_extend("force", opts.setup or {}, {
      ty = function(_, _)
        require("lspconfig").ty.setup({
          settings = { ty = {} },
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
            pyright = { disableOrganizeImports = false },
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
            settings = { loglevel = "error" },
          },
          filetypes = { "python" },
        })
      end,
    })

    return opts
  end,
}
