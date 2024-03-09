# env vars
# shellcheck source=/dev/null
source "$ZDOTDIR"/vars.zsh

# aliases
# shellcheck source=/dev/null
source "$ZDOTDIR"/aliases.zsh

typeset -U path PATH
path=(
    $XDG_DATA_HOME/dw/bin
    $XDG_DATA_HOME/spicetify
    $XDG_DATA_HOME/cargo/bin
    $CARGO_HOME/target/release
    $CARGO_HOME/target/debug
    /home/ervin/bin
    /home/ervin/.local/bin
    /home/ervin/.config/qtile/scripts
    $path
)
export PATH

sa() {
    teriyaki.sh scan
    PHONEIP=$(cat ~/.local/state/phone_ip.log)
    printf "\n"
    ssh "$PHONEIP" -p 8022 -i ~/.ssh/id_rsa
}
