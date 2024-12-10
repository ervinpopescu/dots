function calculator() {
  printf "%s=" "$@"
  printf "%s\n" "$@" | bc -l
}

function mkcd() {
  mkdir "$1"
  cd "$1"
}

function clear_terminal() {
  /bin/clear
  tmux list-sessions &>/dev/null
  ret=$?
  if [ $ret -eq 0 ]; then
    tmux clearhist
  fi
}

function qtile_to_json() {
  python3 -c \
    '''
import sys, json, ast
evald = ast.literal_eval(sys.stdin.read())
if not isinstance(evald, tuple):
  print(json.dumps(evald, indent=2))
else:
  print(json.dumps(ast.literal_eval(evald[1]), indent=2))
'''
}

function get_github_token() {
  keepassxc-cli show ~/.local/share/keepass/Passwords.kdbx "qtile github token" -sa password
}

function birthday_notification() {
  dunstify \
    -a "birthdayNotification" \
    -u normal \
    -r "635325" \
    "$(birthday -W 0 -f ~/.local/share/birthdays)"
}

function services() {
  server-ssh -C 'systemctl status calibre-server calibre-web transmission radarr sonarr jellyfin' |
    grep -E "●|○|Active|Status" |
    /bin/cat
}

function server_last_upg() {server-ssh -C 'pachist.sh | grep upgraded | tail -1 | cut -f1 -d " "'}

function server_du() {server-ssh -C 'df -h -x tmpfs -x devtmpfs -x squashfs'}

function server_status() {
  if ! server-ssh -C 'server-status.py'; then
    echo "server: down"
    return 1
  fi

  echo "------------------------------------------------"
  printf "Last upgrade time: %s\n" "$(server_last_upg)"

  echo "------------------------------------------------"
  printf "Disk usage:\n%s" "$(server_du | tr '\n' '\0' | xargs -0 printf "  %s\n")"
}

function git_last_commits() {
  for branch in $(git branch -r | grep -v HEAD); do
    printf "%-40s\\t%20s\\n" "$branch" "$(git show --format="%h %ci" $branch | head -n 1)"
  done | sort -k3,3 -k4,4 -k5,5
}
