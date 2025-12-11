#!/bin/bash
# Wrapper script to run USB disconnect script as logged-in user
# This runs as root from udev but executes user scripts with proper environment

# Find all users with active graphical sessions
loginctl list-sessions --no-legend 2>/dev/null | while read -r _ _ user _; do
    if [ -n "$user" ] && [ "$user" != "tty" ]; then
        uid=$(id -u "$user" 2>/dev/null)
        if [ -n "$uid" ]; then
            runtime_dir="/run/user/$uid"
            # Run the script directly as the user with proper environment
            runuser -l "$user" -c "export XDG_RUNTIME_DIR=\"$runtime_dir\" DISPLAY=\":0\" PULSE_RUNTIME_PATH=\"$runtime_dir/pulse\"; /opt/system/lib/play-usb-disconnect-sound.sh" 2>/dev/null &
        fi
    fi
done

# Fallback: check for users with runtime directories
for runtime_dir in /run/user/*; do
    if [ -d "$runtime_dir" ]; then
        uid=$(basename "$runtime_dir")
        user=$(getent passwd "$uid" | cut -d: -f1)
        if [ -n "$user" ]; then
            runuser -l "$user" -c "export XDG_RUNTIME_DIR=\"$runtime_dir\" DISPLAY=\":0\" PULSE_RUNTIME_PATH=\"$runtime_dir/pulse\"; /opt/system/lib/play-usb-disconnect-sound.sh" 2>/dev/null &
        fi
    fi
done

