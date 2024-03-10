#!/bin/bash

folder="$(xdg-user-dir PICTURES)/wallpapers/rand"
wallpaper_folder_data="$XDG_DATA_HOME/wallpaper"
cache_until_now="$wallpaper_folder_data/tillnow"
# primary_display_wallpaper="$wallpaper_folder_data/output.png"

set_wall_and_lockscreen() {
	if [[ "$2" == "all" ]]; then
		readarray -t xrandr_output < <(xrandr | grep -w "connected")
		n_displays=${#xrandr_output[@]}
		if [ "$n_displays" -ne 1 ]; then
			readarray -t displays < <(seq 0 $((n_displays - 1)))
		else
			displays=("0")
		fi
	elif [[ "$2" != "" ]]; then
		displays=("$2")
	else
		echo "No displays specified" && exit 1
	fi
	for display in "${displays[@]}"; do
		echo "Setting wallpaper on display $display to $1"
		nitrogen --set-zoom-fill --head="$display" "$1" &>/dev/null && wallpaper_set=1
	done
	# xrandr --dpi 192
	betterlockscreen -u "$1" --fx dimblur && lockscreen_set=1
	[[ $wallpaper_set ]] && [[ $lockscreen_set ]] && notify-send -t 2000 "Wallpaper and lockscreen are set!"
}

case "$1" in
"rand")
	while true; do
		all=$(find "$folder" -maxdepth 1 \( ! -name .gitattributes \) -type f)
		n_all="$(wc -l <<<"$all")"
		shuffled="$(shuf -n "$n_all" <<<"$all")"
		readarray -t already <"$cache_until_now"
		if [ "$((n_all - 1))" -ne "$(wc -l <"$cache_until_now")" ]; then
			wallpaper="$(shuf -n 1 <<<"$shuffled")"
			while [[ "${already[*]}" =~ ${wallpaper} ]]; do
				wallpaper="$(shuf -n 1 <<<"$shuffled")"
			done
		else
			rm "$cache_until_now"
			touch "$cache_until_now"
			wallpaper="$(shuf -n 1 <<<"$shuffled")"
		fi
		set_wall_and_lockscreen "$wallpaper" "$2"
		echo "$wallpaper" >>"$cache_until_now"
		sleep 7200
	done
	;;
*)
	wallpaper="$1"
	{
		set_wall_and_lockscreen "$wallpaper" "$2"
		sleep 2
		xrandr --dpi 96
	} &>"$wallpaper_folder_data/log"
	;;
esac
