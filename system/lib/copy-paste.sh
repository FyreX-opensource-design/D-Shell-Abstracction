#!/bin/sh

# Check if window class is a terminal emulator
is_terminal() {
    window_class="$1"
    # Look for terminal-config.json in $HOME/.config first, then /etc/xdg, else use script directory
    if [ -f "$HOME/.config/terminals.jsonc" ]; then
        config_file="$HOME/.config/terminals.jsonc"
    elif [ -f "/etc/xdg/terminals.jsonc" ]; then
        config_file="/etc/xdg/terminals.jsonc"
    else
        config_file="${0%/*}/terminals.jsonc"
    fi
    
    # If config file doesn't exist, default to checking for alacritty
    if [ ! -f "$config_file" ]; then
        [ "$window_class" = "alacritty" ]
        return
    fi
    
    # Use jq to check if window_class is in the terminal_emulators array
    if command -v jq >/dev/null 2>&1; then
        jq -e --arg class "$window_class" '.terminal_emulators | index($class) != null' "$config_file" >/dev/null 2>&1
    else
        # Fallback: grep through the JSON (less robust but works without jq)
        grep -q "\"$window_class\"" "$config_file"
    fi
}

# Get window ID using the external script
# get_window.sh is in the root of the dotfiles directory
window_id=$("opt/system/lib/get_window.sh" 2>/dev/null)
mode="$1"
if [ "$UNIVERSIAL_COPY_PASTE" = "true" ]; then
    if [ "$mode" = "copy" ]; then
        if is_terminal "$window_id"; then
            echo "keydown ctrl+shift+c" | dotool
            echo "keyup ctrl+shift+c" | dotool
        else
            echo "keydown ctrl+c" | dotool
            echo "keyup ctrl+c" | dotool
        fi
    elif [ "$mode" = "paste" ]; then
        if is_terminal "$window_class"; then
            echo "keydown ctrl+shift+v" | dotool
            echo "keyup ctrl+shift+v" | dotool
        else
            echo "keydown ctrl+v" | dotool
            echo "keyup ctrl+v" | dotool
        fi
    fi
elif [ "$UNIVERSIAL_COPY_PASTE" = "false" ]; then
    if is_terminal "$window_id" && $UNIVERSIAL_COPY_PASTE_NOTIFICATION = "true"; then
        notify-send "Univerisal copy paste not enabled for terminal windows" -u info
        paplay $INFO_SOUND
    fi
    if [ "$mode" = "copy" ]; then
        echo "keydown ctrl+c" | dotool
        echo "keyup ctrl+c" | dotool
    elif [ "$mode" = "paste" ]; then
        echo "keydown ctrl+v" | dotool
        echo "keyup ctrl+v" | dotool
    fi
else 
    notify-send "invalid value for UNIVERSIAL_COPY_PASTE: $UNIVERSIAL_COPY_PASTE" -u critical
    paplay $ERROR_SOUND
    exit 1
fi
