#!/bin/bash
# Stage device-independent firmware in the rootfs for CI.
# uke currently needs no public overrides: GPU and touchscreen firmware comes from
# firmware.tar.gz. This is reserved for future assets such as Wi-Fi BDF files.
set -euo pipefail
rootfs="${1:?usage: stage-public-firmware.sh <rootfs>}"
echo "stage-public-firmware: no uke-specific public firmware to stage"
