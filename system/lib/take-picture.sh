#!/bin/bash

# Take a picture using grim and slurp
/usr/bin/paplay "$SCREENSHOT_SOUND" &
if [ ! -d ~/Pictures/Screenshots ]; then
    mkdir -p ~/Pictures/Screenshots
fi
filename=~/Pictures/Screenshots/$(date +%Y-%m-%d_%H-%M-%S).png
# Use slurp with a unique lockfile to avoid interfering with other slurp processes
LOCKFILE="/tmp/slurp_screenshot.lock"

# Cleanup function to remove lock file
cleanup() {
    rm -f "$LOCKFILE"
}
trap cleanup EXIT

exec 9>"$LOCKFILE"
if ! flock -n 9; then
    echo "Error: Another screenshot selection (slurp) is already running."
    exit 1
fi

# Capture geometry from slurp (user selects area)
geometry=$(slurp 2>/dev/null)
if [ -z "$geometry" ]; then
    # User cancelled selection
    exit 0
fi

# Take screenshot of selected area and copy to clipboard
grim -g "$geometry" "$filename"
wl-copy < "$filename"

if [ "$NOTIFY_SCREENSHOT" = "true" ]; then
    notify-send -u low -i "$filename" "Screenshot taken" "$filename"
fi
