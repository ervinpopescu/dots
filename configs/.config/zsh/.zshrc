# ~/.zshrc file for zsh interactive shells.
# see /usr/share/doc/zsh/examples/zshrc for examples
# shellcheck disable=all

#modules
source "$ZDOTDIR"/keys.zsh
source "$ZDOTDIR"/opts.zsh
source "$ZDOTDIR"/completions.zsh
source "$ZDOTDIR"/prompt.zsh
source "$ZDOTDIR"/command_not_found_handler.zsh
source "$ZDOTDIR"/misc.zsh
source /usr/share/nvm/init-nvm.sh

#plugins
source /usr/share/zsh/plugins/zsh-you-should-use/you-should-use.plugin.zsh
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh
source /usr/share/z/z.sh
# source /usr/share/zsh/plugins/zsh-notify/notify.plugin.zsh
# zstyle ':notify:*' error-icon "https://media3.giphy.com/media/10ECejNtM1GyRy/200_s.gif"
# zstyle ':notify:*' error-title "wow such #fail"
# zstyle ':notify:*' success-icon "https://s-media-cache-ak0.pinimg.com/564x/b5/5a/18/b55a1805f5650495a74202279036ecd2.jpg"
# zstyle ':notify:*' success-title "very #success. wow"
ABBR_TMPDIR=/tmp/zsh-abbr-user/
source /usr/share/zsh/plugins/zsh-abbr/zsh-abbr.zsh
