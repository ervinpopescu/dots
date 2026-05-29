#!/bin/bash

# Configuration
ARCHNET_IP="192.168.1.13"
ARCHNET_MAC="74:40:BB:B8:15:50"
SSH_KEY="$HOME/.ssh/id_rsa_hp"
SSH_USER="ervin"
SSH_HOST="ervinpopescu.ddns.net"
SSH_PORT="5922"

# Dependency checks
for cmd in ping ssh bluetoothctl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: Required command '$cmd' not found." >&2
        exit 1
    fi
done

if ping "$ARCHNET_IP" -c 3 -W 5 &>/dev/null; then
	printf "Starting bluetooth connection to 'archnet'...\n"
	ssh -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "sudo -S start_music.sh"
	sleep 2
    
	if ! bluetoothctl info "$ARCHNET_MAC" | grep -q 'Connected: yes'; then
		bluetoothctl connect "$ARCHNET_MAC" &>/dev/null
		printf "Connected!\n"
	else
		printf "Already connected!\n"
	fi
else
	printf "Stopping bluetooth connection to 'archnet'...\n"
	ssh -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "sudo -S stop_music.sh"
fi
