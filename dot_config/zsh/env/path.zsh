typeset -U path PATH
path=(
    $XDG_DATA_HOME/dw/bin
    $XDG_DATA_HOME/go/bin
    $XDG_DATA_HOME/spicetify
    $XDG_DATA_HOME/cargo/bin
    $CARGO_HOME/target/release
    $CARGO_HOME/target/debug
    $HOME/bin
    $HOME/.local/bin
    $HOME/.config/qtile/scripts
    $HOME/.nimble/bin
    $path
)
export PATH
