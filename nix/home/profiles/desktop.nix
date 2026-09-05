{ ... }:
{
  # Desktop applications remain opt-in until each host is cut over. Native
  # distro packages continue to own the existing desktop stack during the
  # staged migration, avoiding pacman/Nix duplicate binaries.
}
