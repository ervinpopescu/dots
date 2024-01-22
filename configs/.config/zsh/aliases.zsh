# functions
calculator() { printf "%s\n" "$@" | bc -l; }

mkcd() {
    mkdir "$1"
    cd "$1"
}

alias sudo='sudo '

# misc
alias alttab='alttab -w 1 -d 2 -i 140x120 -s 2 -t 140x120 -bg "#1e1d2d" -fg "#d9e0ee" -frame "#ddb6f2" -inact "#1e1d2d" -theme "hicolor"'
alias birthday="birthday -f ~/.local/share/birthdays -W 7"
alias calc="noglob calculator"
alias cat="bat -p"
alias clear="clear; tmux server-info &>/dev/null; [ $? == 1 ] && tmux clearhist"
alias copy="xclip -selection clipboard"
alias cp="cp -v"
alias df="df -h -x tmpfs -x devtmpfs -x squashfs"
alias diff="diff --color=auto --ignore-all-space --ignore-blank-lines --ignore-case --ignore-space-change --ignore-trailing-space --ignore-file-name-case --ignore-tab-expansion"
alias dosbox='dosbox -conf "$XDG_CONFIG_HOME"/dosbox/dosbox.conf'
alias egrep='egrep --color=auto'
alias feh="feh -d --edit --scale-down --auto-zoom -e yudit/23 -M yudit/23"
alias fgrep='fgrep --color=auto'
alias ff='freshfetch; printf "\n\n\n\n\n\n\n\n\\n\n\n\n\n\n\n\n\n\n"'
alias gdb="gdb -q"
alias grep='grep --color=auto'
alias ip='ip --color=auto'
alias less='less -f -r'
alias lf='lfub'
alias md="mdless"
alias mycli="mycli --myclirc ~/.config/mycli/myclirc"
alias mysql-workbench='mysql-workbench --configdir="$XDG_DATA_HOME/mysql/workbench"'
alias ncdu="ncdu --color off --exclude-caches --exclude-kernfs"
alias neo-ru="neo-matrix --color=red --charset=cyrillic -m 'IN SOVIET RUSSIA, COMPUTER PROGRAMS YOU'"
alias neo="neo-matrix -D"
alias nf="neofetch"
alias o="xdg-open"
alias pacgraph='pacgraph -b "#1e1e2e" -l "#81a1c1" -t "#c9cbff" -d "#f38ba8" -n --disable-palette'
alias parallel="parallel-moreutils"
alias rm="rm -rf"
alias soff="sudo suspend-off"
alias son="sudo suspend-on"
alias server-ssh="ssh -i ~/.ssh/id_rsa_hp -p 5922 ervin@ervinpopescu.ddns.net"
alias services='server-ssh systemctl status calibre-server transmission@909{1,2} radarr sonarr jellyfin | grep "●\|○\|Active\|Status" | \cat'
alias sway="sway --unsupported-gpu"
alias systeroid-tui="systeroid-tui --bg-color 1e1e2e"
alias tty-clock="tty-clock -c -C 7 -f '%a, %d %b'"
alias u='sudo pacman -Syu'
alias v="vscodium"
alias vim="nvim"
alias qtile_to_json="python3 -c 'import sys, json, ast; print(json.dumps(ast.literal_eval(sys.stdin.read()), indent=2))'"
alias wget='wget --hsts-file="$XDG_CACHE_HOME/wget-hsts"'
alias xbindkeys='xbindkeys -f $XDG_CONFIG_HOME/xbindkeys/config'

# git
alias gp="git add .; git commit; git push"
alias gsf='git fetch upstream; git checkout master; git merge upstream/master; git push -f'

# power modes
alias cpu-mode-bs="ideapad-perf -p bs"
alias cpu-mode-ic="ideapad-perf -p ic"
alias cpu-mode-ep="ideapad-perf -p ep"

# battery modes
alias bat-mode-bc="ideapad-perf -b bc"
alias bat-mode-off="ideapad-perf -b off"
alias bat-mode-rc="ideapad-perf -b rc"

# bookmarks
while IFS= read -r line; do
    a="$(cut -d" " -f 1 <<< $line)"
    b="$(cut -d" " -f 2 <<< $line)"
    alias "$a"="$b"
    export "$a"="$b"
done < $ZDOTDIR/bookmarks

# ls
alias ls='exa --color=always --icons -H'
alias ll="ls -ghl --accessed --modified"
alias la="ls -a"
alias lla='ll -a'
