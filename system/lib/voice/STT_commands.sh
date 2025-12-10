#!/bin/bash

get_stt_command() {
    command_stt=$(./STT/bin/python3 ./STT.py --model $VOSK_MODEL)
}

if [$command_stt == "take screenshot" || "take a screenshot"] then
    /opt/system/lib/take-picture.sh
fi
if [$command_stt == "open terminal" || "open a terminal"] then
    $TERMINAL &
fi
if [$command_stt == "increment volume" || "increment the volume" || "increase volume" || "increase the volume" || "increase your volume" || "volume up"] then
    /opt/system/lib/volume-ctl.sh add
fi
if [$command_stt == "decrement volume" || "decrement the volume" || "decrease volume" || "decrease the volume" || "decrease your volume" || "volume down"] then
    /opt/system/lib/volume-ctl.sh subtract
fi
if [$command_stt == "toggle volume" || "toggle the volume" || "mute volume" || "mute the volume" || "mute your volume" || "volume mute"] then
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
fi
if [$command_stt == "type" || "type this"] then
    type=$(get_stt_command)
    echo "type $type" | dotool -d
fi