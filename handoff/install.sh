#!/bin/bash
# Hot-load the Xiaomi Focus Keyboard (Nanosic WN8030) on a running kernel.
# Run as root:  sudo /home/saksham/focus-keyboard/install.sh
set -Eeuo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
kver=$(uname -r)
fw=/usr/lib/firmware/nanosic/MCU_Upgrade.bin
moddir=/lib/modules/$kver/extra

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }

echo "== firmware =="
install -Dm644 "$here/MCU_Upgrade.bin" "$fw"
ls -l "$fw"

echo "== modules =="
install -Dm644 "$here/hid-nanosic-wn8030.ko" "$moddir/hid-nanosic-wn8030.ko"
install -Dm644 "$here/uke-kbd-overlay.ko" "$moddir/uke-kbd-overlay.ko"
depmod -a "$kver"
modinfo -F vermagic "$moddir/hid-nanosic-wn8030.ko"
modinfo -F vermagic "$moddir/uke-kbd-overlay.ko"

echo "== driver =="
modprobe hid-nanosic-wn8030 2>/dev/null || insmod "$moddir/hid-nanosic-wn8030.ko"
lsmod | grep -E 'hid_nanosic|hid_multitouch' || true

echo "== device-tree overlay =="
if lsmod | grep -q '^uke_kbd_overlay'; then
    echo "overlay module already loaded"
else
    insmod "$moddir/uke-kbd-overlay.ko"
fi
sleep 2

echo "== i2c controller =="
for d in /sys/bus/platform/devices/*.i2c; do
    [ -e "$d" ] || continue
    name=$(basename "$d")
    case "$name" in
    a8c000.i2c)
        if [ ! -e "$d/driver" ]; then
            echo "$name" > /sys/bus/platform/drivers/geni_i2c/bind 2>/dev/null || true
        fi
        echo "$name -> $(readlink "$d/driver" 2>/dev/null || echo unbound)"
        ;;
    esac
done
for b in /sys/bus/i2c/devices/i2c-*; do
    [ -e "$b/name" ] || continue
    case "$(cat "$b/name")" in
    *a8c000*) echo "bus $(basename "$b") = $(cat "$b/name")";;
    esac
done

echo "== optional auth daemon (not started) =="
install -Dm755 "$here/nanosic-authd.py" /usr/local/sbin/nanosic-authd
install -Dm644 "$here/nanosic-authd.service" /usr/lib/systemd/system/nanosic-authd.service
systemctl daemon-reload
echo "start it with: systemctl enable --now nanosic-authd"

echo "== result =="
sleep 3
dmesg | tail -50
echo "--- input devices ---"
grep -iE 'nanosic|xiaomi|keyboard|touchpad' /proc/bus/input/devices || true
echo "--- leds ---"
ls -l /sys/class/leds/nanosic* 2>/dev/null || true
echo "--- auth node ---"
ls -l /dev/nanosic_auth 2>/dev/null || true
