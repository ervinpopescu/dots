#!/bin/bash

if ping 192.168.1.13 -c 3 -W 5 &>/dev/null
then
	printf '%s\n' Starting bluetooth connection to '`archnet`'...
	ssh -i "$HOME/.ssh/id_rsa_hp" -p 5922 ervin@ervinpopescu.ddns.net sudo -S start_music.sh
	sleep 2
	if ! bluetoothctl info | grep 'Device 74:40:BB:B8:15:50' &>/dev/null
	then
		bluetoothctl connect 74:40:BB:B8:15:50 &>/dev/null
		printf '%s\n' 'Connected!'
	else
		printf '%s\n' 'Already connected!'
	fi
else
	printf '%s\n' Stopping bluetooth connection to '`archnet`'...
	ssh -i "$HOME/.ssh/id_rsa_hp" -p 5922 ervin@ervinpopescu.ddns.net sudo -S stop_music.sh
fi
