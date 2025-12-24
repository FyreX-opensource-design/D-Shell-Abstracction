#!/bin/bash
# Wrapper script to trigger USB connect systemd service as logged-in user
# This runs as root from udev but triggers user systemd services

# Find all users with active graphical sessions
loginctl list-sessions --no-legend 2>/dev/null | while read -r _ _ user _; do
    if [ -n "$user" ] && [ "$user" != "tty" ]; then
        uid=$(id -u "$user" 2>/dev/null)
        if [ -n "$uid" ]; then
            # Trigger the systemd user service
            runuser -l "$user" -c "export XDG_RUNTIME_DIR=/run/user/$uid DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus; systemctl --user start usb-connect-sound.service" 2>/dev/null &
        fi
    fi
done

# Fallback: check for users with runtime directories
for runtime_dir in /run/user/*; do
    if [ -d "$runtime_dir" ]; then
        uid=$(basename "$runtime_dir")
        user=$(getent passwd "$uid" | cut -d: -f1)
        if [ -n "$user" ]; then
            # Trigger the systemd user service
            runuser -l "$user" -c "export XDG_RUNTIME_DIR=$runtime_dir DBUS_SESSION_BUS_ADDRESS=unix:path=$runtime_dir/bus; systemctl --user start usb-connect-sound.service" 2>/dev/null &
        fi
    fi
done

