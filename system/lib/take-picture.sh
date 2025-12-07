#!/bin/bash

# Take a picture using grim and slurp
/usr/bin/paplay $SCREENSHOT_SOUND &
if [ -d "Pictures/Screenshots" ] then
    echo "exists"
else
    mkdir -p ~/Pictures/Screenshots
fi
filename=~/Pictures/Screenshots/$(date +%Y-%m-%d_%H-%M-%S).png
grim -g "$(slurp)" - | tee "$filename" | wl-copy
if [ $NOTIFY_SCREENSHOT -eq 1 ]; then
    notify-send -u low -i "$filename" "Screenshot taken" "$filename"
fi
