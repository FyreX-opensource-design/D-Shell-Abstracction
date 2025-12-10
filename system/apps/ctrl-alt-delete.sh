$options = "Shutdown\nReboot\nLogout"
if [ $TASK_MANAGER -v ] then
    $options += "\nTask Manager"
fi
SELECTED_OPTION=$(printf "$options" | wofi show --dmenu -p Options: -s "$WOFI_THEME/wofi/style.css")

case $SELECTED_OPTION in
    "Shutdown")
        systemctl poweroff
        ;;
    "Reboot")
        systemctl reboot
        ;;
    "Logout")
        systemctl logout --force
        ;;
    "Task Manager")
        $TASK_MANAGER
        ;;
esac