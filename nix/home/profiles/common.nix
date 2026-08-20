{ lib, pkgs, profile, ... }:
let
  capabilities = import ../../lib/profiles.nix { inherit profile; };
in
{
  home.stateVersion = "25.11";
  programs.home-manager.enable = true;

  home.packages = with pkgs; [
    bash
    bat
    curl
    eza
    fd
    fzf
    git
    git-lfs
    jq
    ripgrep
    tmux
    wget
    zsh
  ] ++ lib.optionals (capabilities.hasBattery && capabilities.isLinux) [ acpi ]
    ++ lib.optionals capabilities.isServer [ openssh ];

  home.sessionVariables = {
    EDITOR = "nvim";
    VISUAL = "nvim";
  };
}
