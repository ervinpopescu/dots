#!/bin/bash

line="$(dig -4 TXT +short o-o.myaddr.l.google.com @ns1.google.com | tr -d '"') home"
sed -i "s/.* home/$line/" /etc/hosts
