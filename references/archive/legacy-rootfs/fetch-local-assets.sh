#!/bin/bash
# Build local-assets/ (firmware, modules, SSH key) from a connected tablet
# or extracted stock firmware. Requires adb and root access.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(dirname "$script_dir")"
assets="$repo_dir/local-assets"
kver="${UKE_KERNEL_VERSION:-7.2.0-rc2-uke}"
mkdir -p "$assets/modules" "$assets/boot-files"
# firmware from rootfs/firmware.tar.gz (or extracted stock firmware)
if [ -f "$repo_dir/rootfs/firmware.tar.gz" ]; then
	cp -v "$repo_dir/rootfs/firmware.tar.gz" "$assets/firmware.tar.gz"
fi
# modules from build/uke-modules
if [ -d "$repo_dir/build/uke-modules/usr/lib/modules/$kver" ]; then
	cp -a "$repo_dir/build/uke-modules/usr/lib/modules/$kver" "$assets/modules/"
fi
# SSH key
[ -f "$HOME/.ssh/id_ed25519.pub" ] && cp -v "$HOME/.ssh/id_ed25519.pub" "$assets/ssh-key.pub" || true
echo "local-assets ready: $assets"
