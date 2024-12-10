# bookmarks
while IFS= read -r line; do
    x="$(cut -d" " -f 1 <<< $line)"
    y="$(cut -d" " -f 2 <<< $line)"
    alias $x="$HOME/$y"
    export $x="$HOME/$y"
done < $ZDOTDIR/files/bookmarks
