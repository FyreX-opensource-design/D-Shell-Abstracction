/usr/bin/paplay $USB_DISCONNECT_SOUND &

if [ $SEND_USB_NOTIFICATION = "true" ]; then
    notify-send -i $USB_DISCONNECT_ICON "USB Device Disonnected" "The USB device has been disconnected."
fi  
