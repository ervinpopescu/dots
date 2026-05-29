#!/bin/bash

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)."
  exit 1
fi

# Get new IP for the domain
new_ip=$(dig -4 TXT +short o-o.myaddr.l.google.com @ns1.google.com | tr -d '"')

if [ -z "$new_ip" ]; then
    echo "Error: Could not fetch new IP."
    exit 1
fi

echo "Updating /etc/hosts with new IP: $new_ip"

# Detect OS for sed syntax
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires an extension argument for -i (empty string for no backup)
    sed -i '' "s/.* home/$new_ip home/" /etc/hosts
else
    # GNU sed (Linux)
    sed -i "s/.* home/$new_ip home/" /etc/hosts
fi
