#!/bin/bash

# Configuration
PHONE_MAC="54:67:06:f1:ce:9f"
PHONE_KEY="$HOME/.ssh/id_rsa"
IP_LOG="$HOME/.local/state/phone_ip.log"

# Dependency checks
check_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: Required command '$1' not found." >&2
        return 1
    fi
}

# Fetch Phone IP from log
if [ -f "$IP_LOG" ]; then
    phone_ip=$(cat "$IP_LOG")
elif [ "$1" != "scan" ]; then
    echo "No ip log found, run 'teriyaki.sh scan' first." >&2
    exit 1
fi

PHONE_SSH="ssh -p 8022 -i $PHONE_KEY $phone_ip"

case "$1" in
    run)
        shift
        eval "$PHONE_SSH $*"
        ;;
    cp-set)
        eval "$PHONE_SSH termux-clipboard-set '$2'"
        ;;
    cp-get)
        eval "$PHONE_SSH termux-clipboard-get"
        ;;
    pull)
        check_cmd scp || exit 1
        scp -P 8022 -o ConnectTimeout=10 -i "$PHONE_KEY" "$phone_ip:$2" "$3"
        ;;
    push)
        check_cmd scp || exit 1
        scp -P 8022 -o ConnectTimeout=10 -i "$PHONE_KEY" "$2" "$phone_ip:$3"
        ;;
    share)
        eval "$PHONE_SSH rm -rf /data/data/com.termux/files/usr/tmp/*"
        check_cmd scp || exit 1
        scp -P 8022 -i "$PHONE_KEY" "$2" "$phone_ip:/data/data/com.termux/files/usr/tmp"
        eval "$PHONE_SSH termux-share /data/data/com.termux/files/usr/tmp/*"
        ;;
    mount)
        check_cmd sshfs || exit 1
        sshfs -p 8022 -o IdentityFile="$PHONE_KEY" "$phone_ip:$2" "$3"
        ;;
    scan)
        check_cmd arp-scan || exit 1
        printf "Updating the IP address...\n"
        gateway=$(ip r | grep -vwE '(default)' | awk '{print $1}')
        if [ -z "$gateway" ]; then gateway="192.168.1.0/24"; fi
        
        PHONE_IP=$(sudo arp-scan "$gateway" | grep -i "$PHONE_MAC" | awk '{print $1}')
        if [ -z "$PHONE_IP" ]; then
            printf "Couldn't find device's IP address. Make sure it's connected and screen is on.\n" >&2
            exit 127
        fi
        mkdir -p "$(dirname "$IP_LOG")"
        echo "$PHONE_IP" > "$IP_LOG"
        printf "Updated! Current phone ip is: %s\n" "$PHONE_IP"
        ;;
    sms)
        check_cmd jq || exit 1
        eval "$PHONE_SSH termux-sms-list -l 1" | jq -r '.[0]["body"]'
        ;;
    wallpaper)
        eval "$PHONE_SSH termux-wallpaper -f storage/downloads/wall"
        eval "$PHONE_SSH termux-wallpaper -f storage/downloads/wall -l"
        ;;
    *)
        printf "Mini Termux Controller

    scan                -  scan network to update phone's current IP address
    run <param>         -  run ssh commands
    cp-set <string>     -  copy the string to phone clipboard
    cp-get              -  return the string from phone clipboard
    sms                 -  display latest sms (requires root/termux-api)
    pull  <src> <dest>  -  pull file from phone
    push  <src> <dest>  -  push file to phone
    share <src>         -  share file via phone apps
    mount <src> <dest>  -  mount phone folder via SSHFS
"
    ;;
esac
