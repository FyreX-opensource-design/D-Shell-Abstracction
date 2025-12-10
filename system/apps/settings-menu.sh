$options = ""
if [ $VOLUME_CONTROL -v ] then
    $options += "Audio settings\n"
fi
if [ openrgb -v ] then
    $options += "RGB settings\n"
fi
if [ opentabletdriver -v ] then
    $options += "Tablet settings\n"
fi
if [ oversteer -v ] then
    $options += "Oversteer settings\n"
fi
if [ wdisplays -v ] then
    $options += "Display settings\n"
fi
if [ opendeck -v ] then
    $options += "Streamdeck settings\n"
fi
if [ $TASK_MANAGER -v ] then
    $options += "Task Manager\n"
fi
if [ $BLUETOOTH -v ] then
    $options += "Bluetooth\n"
fi
$options += "WiFi settings\n"

SELECTED_OPTION=$(printf "$options" | wofi show --dmenu -p Options: -s "$WOFI_THEME/wofi/style.css")

case $SELECTED_OPTION in
    "Audio settings")
        $VOLUME_CONTROL
        ;;
    "RGB settings")
        openrgb
        ;;
    "Tablet settings")
        opentabletdriver
        ;;
    "Oversteer settings")
        oversteer
        ;;
    "Display settings")
        wdisplays
        ;;
    "Streamdeck settings")
        opendeck
        ;;
    "Task Manager")
        $TASK_MANAGER
        ;;
    "WiFi settings")
        /opt/system/apps/wofi-wifi-menu.sh
        ;;
    "Bluetooth")
        $BLUETOOTH
        ;;
esac