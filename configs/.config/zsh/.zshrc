# ~/.zshrc file for zsh interactive shells.
# see /usr/share/doc/zsh/examples/zshrc for examples
# shellcheck disable=all

#modules
source "$ZDOTDIR"/keys.zsh
source "$ZDOTDIR"/opts.zsh
source "$ZDOTDIR"/completions.zsh
source "$ZDOTDIR"/prompt.zsh
source "$ZDOTDIR"/misc.zsh

#plugins
[ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
[ -f /usr/share/z/z.sh ] && source /usr/share/z/z.sh
# source /usr/share/zsh/plugins/zsh-notify/notify.plugin.zsh
# zstyle ':notify:*' error-icon "https://media3.giphy.com/media/10ECejNtM1GyRy/200_s.gif"
# zstyle ':notify:*' error-title "wow such #fail"
# zstyle ':notify:*' success-icon "https://s-media-cache-ak0.pinimg.com/564x/b5/5a/18/b55a1805f5650495a74202279036ecd2.jpg"
# zstyle ':notify:*' success-title "very #success. wow"
ABBR_TMPDIR=/tmp/zsh-abbr-user/
[ -f /usr/share/zsh/plugins/zsh-abbr/zsh-abbr.zsh ] && source /usr/share/zsh/plugins/zsh-abbr/zsh-abbr.zsh
