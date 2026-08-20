{ pkgs, ... }:
let
  # GCC and the full Clang wrapper both provide ld.bfd. Expose Clang's
  # compilers and language server without colliding in Home Manager's profile.
  clangTools = pkgs.runCommand "clang-tools-only" { } ''
    mkdir -p $out/bin
    for tool in clang clang++ clang-cpp clangd; do
      ln -s ${pkgs.clang}/bin/$tool $out/bin/$tool
    done
  '';
in
{
  # This is the intentionally small, shared developer baseline. Project
  # dependencies belong in each project's flake or development shell.
  home.packages = with pkgs; [
    # Git and repository tooling
    gh
    delta
    lazygit

    # Editors and terminal tooling
    neovim
    zsh-completions
    direnv
    just
    yq-go

    # Language runtimes
    python3
    nodejs
    go
    rustc
    cargo
    jdk17
    zig

    # Native build tooling
    gcc
    clangTools
    gnumake
    cmake
    meson
    ninja
    ccache
    pkg-config
    autoconf
    automake
    bison
    flex
    nasm
    swig

    # Repository quality tooling
    pre-commit
    shellcheck
    shfmt
    stylua
    taplo
    ruff
    pyright
    mypy
  ];
}
