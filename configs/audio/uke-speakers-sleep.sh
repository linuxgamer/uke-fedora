#!/bin/sh
# systemd-sleep hook: re-enable speakers after suspend/hibernate resume
case "$1" in
    post)
        # Wait for sound card to reinitialize
        sleep 2
        amixer -c 0 cset numid=55 1 >/dev/null 2>&1  # TopLeft Speaker Switch
        amixer -c 0 cset numid=58 1 >/dev/null 2>&1  # TopRight Speaker Switch
        amixer -c 0 cset numid=61 1 >/dev/null 2>&1  # BottomLeft Speaker Switch
        amixer -c 0 cset numid=64 1 >/dev/null 2>&1  # BottomRight Speaker Switch
        amixer -c 0 cset numid=13 1 >/dev/null 2>&1  # CLSH Switch
        amixer -c 0 cset numid=19 1 >/dev/null 2>&1  # LDOH Enable Switch
        ;;
esac
