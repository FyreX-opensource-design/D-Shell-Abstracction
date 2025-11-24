#add args for adding and subtracting volume

if [ "$1" == "add" ]; then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
    /usr/bin/paplay $VOLUME_SOUND &
elif [ "$1" == "subtract" ]; then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
    /usr/bin/paplay $VOLUME_SOUND &
fi
