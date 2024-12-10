autoload -Uz add-zsh-hook

add-zsh-hook -Uz precmd () {
    printf '%b' '\e[0m\e(B\e)0\017\e[?5l\e7\e[0;0r\e8'
}

add-zsh-hook -Uz chpwd (){ lla;}

if [[ -d "$TMUX_PLUGIN_MANAGER_PATH" ]]; then
  add-zsh-hook chpwd tmux-window-name () {
	($TMUX_PLUGIN_MANAGER_PATH/tmux-window-name/scripts/rename_session_windows.py &)
}
fi
