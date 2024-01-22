#!/bin/bash
PHONE_MAC="54:67:06:f1:ce:9f"   # You can get phone's mac address from status section in android settings.
PHONE_KEY="$HOME/.ssh/id_rsa"   # SSH secret key to use while connecting to phone.

if [ -e "$HOME/.local/state/phone_ip.log" ] # Check if previous tmp file exists
    then phone_ip=$(cat "$HOME/.local/state/phone_ip.log")
elif [ "$1" != "scan" ]
    then printf '%s\n' "No ip log found, run 'teriyaki.sh scan' first."; exit 1
fi

PHONE_SSH="ssh $phone_ip -p 8022 -i $PHONE_KEY"

case $1 in
    run)
        eval "$PHONE_SSH ${*:2}"
        ;;
    cp-set)
        eval "$PHONE_SSH termux-clipboard-set '$2'"
        ;;
    cp-get)
        $PHONE_SSH termux-clipboard-get
        ;;
    pull)
        scp -P 8022 -o ConnectTimeout=10 -i "$PHONE_KEY" "$phone_ip":"$2" "$3"
        ;;
    push)
        scp -P 8022 -o ConnectTimeout=10 -i "$PHONE_KEY" "$2" "$phone_ip":"$3"
        ;;
    share)
        $PHONE_SSH rm -rf /data/data/com.termux/files/usr/tmp/*
        scp -P 8022 -i "$PHONE_KEY" "$2" "$phone_ip":/data/data/com.termux/files/usr/tmp
        $PHONE_SSH termux-share /data/data/com.termux/files/usr/tmp/*
        ;;
    mount)
        sshfs -p 8022 -o IdentityFile="$PHONE_KEY" "$phone_ip":"$2" "$3"
        ;;
    scan)
        printf "Updating the IP address...\n"
        gateway=$(ip r | grep -vwE '(default)' | awk '{print $1}')
        PHONE_IP=$(sudo arp-scan "$gateway" | grep $PHONE_MAC | awk '{print $1}')
        if [[ ! -v PHONE_IP ]]; then
            printf '%s\n' "Couldn't find device's ip address. Make sure it's connected to network and try again while phone screen is on."
            exit 127
        fi
        printf '%s\n' "$PHONE_IP" > "$HOME/.local/state/phone_ip.log"
        printf "%s" "Updated! Current phone ip is: $PHONE_IP"
        ;;
    sms)
        $PHONE_SSH termux-sms-list -l 1 | jq -r '.[0]["body"]'
        ;;
    wallpaper)
        $PHONE_SSH termux-wallpaper -f storage/downloads/wall
        $PHONE_SSH termux-wallpaper -f storage/downloads/wall -l
        ;;
    *)
        printf '%s\n' "Mini Termux Controller

    scan                -  scan network to update phone's current IP address
    run <param>         -  run ssh commands or connect ssh terminal if no arg passed
    cp-set <string>     -  copy the string to phone clipboard
    cp-get              -  return the string from phone clipboard
    sms                 -  display latest sms, useful for verification codes (root)
    pull  <src> <dest>  -  pull the file from phone to computer
    push  <src> <dest>  -  push the file to phone from computer
    share <src>         -  share the media from computer to phone apps like whatsapp, telegram
    mount <src> <dest>  -  use SSHFS to mount specific phone folder to linux folder
"
    ;;
esac
