autoload -Uz add-zsh-hook

precmd_reset_terminal() {
    printf '%b' '\e[0m\e(B\e)0\017\e[?5l\e7\e[0;0r\e8'
}
add-zsh-hook -Uz precmd precmd_reset_terminal

chpwd_list() {
  lla
}
add-zsh-hook chpwd chpwd_list
