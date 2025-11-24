/usr/bin/paplay $USB_CONNECT_SOUND &

if [ $SEND_USB_NOTIFICATION = "true" ]; then
    notify-send -i $USB_CONNECT_ICON "USB Device Connected" "The USB device has been connected."
fi  