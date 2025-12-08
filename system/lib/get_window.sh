#!/bin/sh

# Check for wl-roots compositors first
if pgrep -x "wayfire" >/dev/null || pgrep -x "sway" >/dev/null || pgrep -x "river" >/dev/null || pgrep -x "labwc" >/dev/null || pgrep -x "wlrctl" >/dev/null; then
    wlrctl window list state:focused | awk '{print $1}' | sed 's/:$//'
# If not, check for Hyprland and use its method
elif pgrep -x "Hyprland" >/dev/null; then
    # Use hyprctl to get the address of the focused window
    hyprctl activewindow -j | awk -F'"' '/"address":/ {print $4}'
else
    echo "No supported Wayland compositor detected (wl-roots [wayfire, sway, river, labwc] or Hyprland)."
    exit 1
fi