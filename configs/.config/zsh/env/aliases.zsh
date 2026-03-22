alias sudo='sudo '

# misc
alias adb='HOME="$XDG_DATA_HOME"/android adb'
alias birthday="birthday -f ~/.local/share/birthdays -W 7"
alias calc="noglob calculator"
alias cat="bat -p"
alias clear="clear_terminal"
alias copy="xclip -selection clipboard"
alias code="code --extensions-dir \"$XDG_DATA_HOME/vscode\""
alias cp="cp -vi"
alias df="df -h -x tmpfs -x devtmpfs -x squashfs"
alias diff="diff --color=auto --ignore-all-space --ignore-blank-lines --ignore-case --ignore-space-change --ignore-trailing-space --ignore-file-name-case --ignore-tab-expansion"
alias dosbox='dosbox -conf "$XDG_CONFIG_HOME"/dosbox/dosbox.conf'
alias egrep='egrep --color=auto'
alias feh="feh -d --edit --scale-down --auto-zoom -e yudit/23 -M yudit/23"
alias fgrep='fgrep --color=auto'
alias ff='freshfetch; printf "\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n"'
alias gdb="gdb -q"
alias grep='rg --color=auto'
alias ip='ip --color=auto'
alias jess="jq -C | less -r"
alias less='less -f -r'
alias lf='lfub'
alias mdless="PAGER='less -r' mdless"
alias mycli="mycli --myclirc ~/.config/mycli/myclirc"
alias mysql-workbench='mysql-workbench --configdir="$XDG_DATA_HOME/mysql/workbench"'
alias ncdu="ncdu --color off --exclude-caches --exclude-kernfs"
alias neo-ru="neo-matrix --color=red --charset=cyrillic -m 'IN SOVIET RUSSIA, COMPUTER PROGRAMS YOU'"
alias neo="neo-matrix -D"
alias nf="neofetch"
alias o="xdg-open"
alias pacdiff="sudo DIFFPROG='nvim -d -u /home/ervin/.config/nvim/init.lua' pacdiff"
alias pacgraph='pacgraph -b "#1e1e2e" -l "#81a1c1" -t "#c9cbff" -d "#f38ba8" -n --disable-palette'
alias parallel="parallel-moreutils"
alias rm="rm -ri"
alias stg="sudo suspend-toggle"
alias sway="sway --unsupported-gpu"
alias systeroid-tui="systeroid-tui --bg-color 1e1e2e"
alias tty-clock="tty-clock -c -C 7 -f '%a, %d %b'"
alias u='sudo pacman -Syu'
alias v="vscodium"
alias vim="nvim"
alias wget='wget --hsts-file="$XDG_CACHE_HOME/wget-hsts"'
alias xbindkeys='xbindkeys -f $XDG_CONFIG_HOME/xbindkeys/config'

# # git
# alias gp="git add .; git commit; git push"
# alias gsf='git fetch upstream; git checkout master; git merge upstream/master; git push -f'

# power modes
alias cpu-mode-bs="ideapad-perf -p bs"
alias cpu-mode-ic="ideapad-perf -p ic"
alias cpu-mode-ep="ideapad-perf -p ep"

# battery modes
alias bat-mode-bc="ideapad-perf -b bc"
alias bat-mode-off="ideapad-perf -b off"
alias bat-mode-rc="ideapad-perf -b rc"

# ls
alias ls='exa --color=always --icons -H'
alias ll="ls -ghl --accessed --modified"
alias la="ls -a"
alias lla='ll -a'
