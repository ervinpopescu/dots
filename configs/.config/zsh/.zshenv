typeset -U path PATH
path=(
    /home/ervin/.local/share/dw/bin
    /home/ervin/bin
    /home/ervin/.local/share/spicetify
    /home/ervin/.local/bin
    /home/ervin/.config/qtile-x11/scripts
    $path
)
export PATH

# env vars
# shellcheck source=/dev/null
source "$ZDOTDIR"/vars.zsh

# aliases
# shellcheck source=/dev/null
source "$ZDOTDIR"/aliases.zsh

sa(){
    teriyaki.sh scan
    PHONEIP=$(cat ~/.local/state/phone_ip.log)
    printf "\n"
    ssh "$PHONEIP" -p 8022 -i ~/.ssh/id_rsa
}
