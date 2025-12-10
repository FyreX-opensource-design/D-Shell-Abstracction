#!/bin/bash

mode=$1
if [ $mode != "ctrl" && $mode != "alt" && $mode != "shift" && $mode != "super" ]; then
    echo "Invalid mode: $mode. Valid modes are: ctrl, alt, shift, and super."
    exit 1
fi
if $STICKY_KEYS == "true"; then
    if [ "$mode" == "ctrl" ]; then
        if [ "$_STICKY_KEYS_CTRL" == "true" ]; then
            export _STICKY_KEYS_CTRL="false"
            echo "keyup ctrl" | dotool
            $toggle = "disabled"
        else
            export _STICKY_KEYS_CTRL="true"
            echo "keydown ctrl" | dotool
            $toggle = "enabled"
        fi
    elif [ "$mode" == "alt" ]; then
        if [ "$_STICKY_KEYS_ALT" == "true" ]; then
            export _STICKY_KEYS_ALT="false"
            echo "keyup alt" | dotool
            $toggle = "disabled"
        else
            export _STICKY_KEYS_ALT="true"
            echo "keydown alt" | dotool
            $toggle = "enabled"
        fi
    elif [ "$mode" == "shift" ]; then
        if [ "$_STICKY_KEYS_SHIFT" == "true" ]; then
            export _STICKY_KEYS_SHIFT="false"
            echo "keyup shift" | dotool
            $toggle = "disabled"
        else
            export _STICKY_KEYS_SHIFT="true"
            echo "keydown shift" | dotool
            $toggle = "enabled"
        fi
    elif [ "$mode" == "super" ]; then
        if [ "$_STICKY_KEYS_SUPER" == "true" ]; then
            export _STICKY_KEYS_SUPER="false"
            echo "keyup super" | dotool
            $toggle = "disabled"
        else
            export _STICKY_KEYS_SUPER="true"
            echo "keydown super" | dotool
            $toggle = "enabled"
        fi
    fi
    notify-send "Sticky key $mode is $toggle" -u info -i $INFO_ICON -p 2000
    paplay $INFO_SOUND
else
    export _STICKY_KEYS_CTRL="false"
    export _STICKY_KEYS_ALT="false"
    export _STICKY_KEYS_SHIFT="false"
fi