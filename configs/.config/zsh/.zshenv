typeset -U path PATH
path=(
    $HOME/bin
    $HOME/.local/bin
    $HOME/.config/qtile/scripts
    $path
)
export PATH

# env vars
# shellcheck source=/dev/null
source "$ZDOTDIR"/vars.zsh

# aliases
# shellcheck source=/dev/null
source "$ZDOTDIR"/aliases.zsh
