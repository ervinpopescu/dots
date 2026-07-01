# Session notes

- `is_arch` is referenced in `dot_config/zsh/dot_zshrc.tmpl` and
  `dot_config/zsh/rc/command_not_found_handler.zsh.tmpl` but is never
  defined in `.chezmoi.toml.tmpl`'s `[data]` block. Go templates treat a
  missing map key as falsy, so `{{ if .is_arch }}` is always false on
  every machine — including lenovo/cloudtop, which are Arch and should
  get the pacman-based `command_not_found_handler`. Likely needs
  `is_arch = {{ or (eq $machine "lenovo") (eq $machine "cloudtop") }}`
  (or similar) added to `.chezmoi.toml.tmpl`.
