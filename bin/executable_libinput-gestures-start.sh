#!/bin/bash

if [[ "$XDG_SESSION_DESKTOP" = "qtile" ]]
then
  rm "$HOME"/.config/libinput-gestures.conf
  ln -s "$HOME"/.config/libinput-gestures-qtile.conf "$HOME"/.config/libinput-gestures.conf
  libinput-gestures-setup restart
else
  rm "$HOME"/.config/libinput-gestures.conf
  ln -s "$HOME"/.config/libinput-gestures-budgie.conf "$HOME"/.config/libinput-gestures.conf
  libinput-gestures-setup restart
fi
