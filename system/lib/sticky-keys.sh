#!/bin/bash

# State file to persist sticky key states
STATE_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/sticky-keys-state"
# Lock file to prevent concurrent execution
LOCK_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/sticky-keys.lock"

# Ensure cache directory exists
mkdir -p "$(dirname "$LOCK_FILE")"

# Function to ensure dotoold daemon is running
ensure_dotoold() {
    if ! pgrep -x dotoold >/dev/null 2>&1; then
        dotoold >/dev/null 2>&1 &
        sleep 0.15
    fi
}

# Function to send command to dotool daemon
send_to_dotool() {
    ensure_dotoold
    echo "$1" | dotoolc 2>/dev/null
}

# Ensure daemon is ready before proceeding
ensure_dotoold

# Acquire lock using flock (file descriptor 200)
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "Another instance is already running. Exiting."
    exit 1
fi

# Ensure lock is released on script exit (keep daemon running for reuse)
trap 'flock -u 200; exit' INT TERM EXIT

# Load state from file if it exists
if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"
fi

# Initialize state variables if they don't exist
_STICKY_KEYS_CTRL="${_STICKY_KEYS_CTRL:-false}"
_STICKY_KEYS_ALT="${_STICKY_KEYS_ALT:-false}"
_STICKY_KEYS_SHIFT="${_STICKY_KEYS_SHIFT:-false}"
_STICKY_KEYS_SUPER="${_STICKY_KEYS_SUPER:-false}"

mode=$1
trigger="${2:-release}"  # Default to "release" if not specified

if [[ "$mode" != "ctrl" && "$mode" != "alt" && "$mode" != "shift" && "$mode" != "super" ]]; then
    echo "Invalid mode: $mode. Valid modes are: ctrl, alt, shift, and super."
    exit 1
fi

# We only handle release events now (press bindings removed to avoid consuming key events)
if [ "$trigger" != "release" ]; then
    exit 0
fi

# Function to save state to file
save_state() {
    mkdir -p "$(dirname "$STATE_FILE")"
    cat > "$STATE_FILE" <<EOF
_STICKY_KEYS_CTRL="$1"
_STICKY_KEYS_ALT="$2"
_STICKY_KEYS_SHIFT="$3"
_STICKY_KEYS_SUPER="$4"
EOF
}

if [ "$STICKY_KEYS" = "true" ]; then
    if [ "$mode" = "ctrl" ]; then
        if [ "$_STICKY_KEYS_CTRL" = "true" ]; then
            _STICKY_KEYS_CTRL="false"
            send_to_dotool "keyup leftctrl"
            toggle="disabled"
        else
            _STICKY_KEYS_CTRL="true"
            send_to_dotool "keydown leftctrl"
            toggle="enabled"
        fi
        save_state "$_STICKY_KEYS_CTRL" "$_STICKY_KEYS_ALT" "$_STICKY_KEYS_SHIFT" "$_STICKY_KEYS_SUPER"
    elif [ "$mode" = "alt" ]; then
        if [ "$_STICKY_KEYS_ALT" = "true" ]; then
            _STICKY_KEYS_ALT="false"
            send_to_dotool "keyup leftalt"
            toggle="disabled"
        else
            _STICKY_KEYS_ALT="true"
            send_to_dotool "keydown leftalt"
            toggle="enabled"
        fi
        save_state "$_STICKY_KEYS_CTRL" "$_STICKY_KEYS_ALT" "$_STICKY_KEYS_SHIFT" "$_STICKY_KEYS_SUPER"
    elif [ "$mode" = "shift" ]; then
        if [ "$_STICKY_KEYS_SHIFT" = "true" ]; then
            _STICKY_KEYS_SHIFT="false"
            send_to_dotool "keyup leftshift"
            toggle="disabled"
        else
            _STICKY_KEYS_SHIFT="true"
            send_to_dotool "keydown leftshift"
            toggle="enabled"
        fi
        save_state "$_STICKY_KEYS_CTRL" "$_STICKY_KEYS_ALT" "$_STICKY_KEYS_SHIFT" "$_STICKY_KEYS_SUPER"
    elif [ "$mode" = "super" ]; then
        if [ "$_STICKY_KEYS_SUPER" = "true" ]; then
            _STICKY_KEYS_SUPER="false"
            send_to_dotool "keyup leftmeta"
            toggle="disabled"
        else
            _STICKY_KEYS_SUPER="true"
            send_to_dotool "keydown leftmeta"
            toggle="enabled"
        fi
        save_state "$_STICKY_KEYS_CTRL" "$_STICKY_KEYS_ALT" "$_STICKY_KEYS_SHIFT" "$_STICKY_KEYS_SUPER"
    fi
    notify-send "Sticky key $mode is $toggle" -u normal -i "$INFO_ICON" -t 2000
    paplay $INFO_SOUND
else
    # When sticky keys is disabled, simulate a normal key press on release
    # This allows key mappings in rc.xml to work normally
    # First ensure the key is released (in case it's stuck)
    case "$mode" in
        ctrl)
            send_to_dotool "keyup leftctrl"
            sleep 0.02
            send_to_dotool "keydown leftctrl"
            sleep 0.05
            send_to_dotool "keyup leftctrl"
            ;;
        alt)
            send_to_dotool "keyup leftalt"
            sleep 0.02
            send_to_dotool "keydown leftalt"
            sleep 0.05
            send_to_dotool "keyup leftalt"
            ;;
        shift)
            send_to_dotool "keyup leftshift"
            sleep 0.02
            send_to_dotool "keydown leftshift"
            sleep 0.05
            send_to_dotool "keyup leftshift"
            ;;
        super)
            send_to_dotool "keyup leftmeta"
            sleep 0.02
            send_to_dotool "keydown leftmeta"
            sleep 0.05
            send_to_dotool "keyup leftmeta"
            ;;
    esac
    # Reset all states when sticky keys is disabled
    _STICKY_KEYS_CTRL="false"
    _STICKY_KEYS_ALT="false"
    _STICKY_KEYS_SHIFT="false"
    _STICKY_KEYS_SUPER="false"
    save_state "$_STICKY_KEYS_CTRL" "$_STICKY_KEYS_ALT" "$_STICKY_KEYS_SHIFT" "$_STICKY_KEYS_SUPER"
fi