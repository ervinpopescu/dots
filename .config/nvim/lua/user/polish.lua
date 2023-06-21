-- This function is run last and is a good place to configuring
-- augroups/autocommands and custom filetypes also this just pure lua so
-- anything that doesn't fit in the normal config locations above can go here

return function()
  vim.g.catppuccin_flavour = "mocha"
  vim.g.octave_highlight_variables = 1
  vim.g.octave_highlight_operators = 1
  vim.g.octave_highlight_tabs = 1
  require "user.autocmds"
end
