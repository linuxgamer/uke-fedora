#!/bin/bash
# Застейджить device-независимый firmware в rootfs (для CI).
# Для uke публичные overrides пока не нужны: GPU/тач firmware идёт из
# firmware.tar.gz. Здесь место для будущих (Wi-Fi BDF и т.п.).
set -euo pipefail
rootfs="${1:?usage: stage-public-firmware.sh <rootfs>}"
echo "stage-public-firmware: для uke пока no-op"
