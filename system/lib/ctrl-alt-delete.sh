SELECTED_OPTION=$(printf "Shutdown\nReboot\nLogout\nTask Manager" | wofi show --dmenu -p Options: -s "$WOFI_THEME/wofi/style.css")

case $SELECTED_OPTION in
    "Shutdown")
        systemctl poweroff
        ;;
    "Reboot")
        systemctl reboot
        ;;
    "Logout")
        swaymsg logout --force
        ;;
    "Task Manager")
        $TASK_MANAGER
        ;;
esac