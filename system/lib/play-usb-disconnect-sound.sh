#!/bin/bash

# Start paplay in background so notification can be sent immediately
/usr/bin/paplay "$USB_DISCONNECT_SOUND" &
paplay_pid=$!

if [ "$SEND_USB_NOTIFICATION" = "true" ]; then
    notify-send -i "$USB_DISCONNECT_ICON" "USB Device Disconnected" "The USB device has been disconnected."
fi

# Wait for paplay to finish so systemd doesn't kill it
wait $paplay_pid
