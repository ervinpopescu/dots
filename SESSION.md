# Remaining macOS XDG Ninja findings

- XDG Ninja's npm output suggests `tmp=${XDG_RUNTIME_DIR}/npm`; this is
  intentionally omitted because recent npm versions removed the option and warn
  when it is configured.
- XDG Ninja recommends `/run/user/$UID` for `XDG_RUNTIME_DIR`, which is
  Linux-specific. The macOS system ZSH file uses a private directory below
  `${TMPDIR:-/tmp}` instead.
- AnyDesk and Swift Package Manager remain unsupported by XDG Ninja on macOS;
  `.ssh` is an expected home-directory location for OpenSSH and is not moved.
