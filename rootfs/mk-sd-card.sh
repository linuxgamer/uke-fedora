#!/bin/bash
# Rescue microSD с Fedora rootfs для uke (фаза 1).
#   sudo ./rootfs/mk-sd-card.sh <rootfs.tar.gz> <output.img|/dev/sdX> [sizeGiB]
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "запусти под root (sudo)" >&2; exit 1; }
script_dir="$(cd "$(dirname "$0")" && pwd)"; repo_dir="$(dirname "$script_dir")"
rootfs_tar="${1:?usage: mk-sd-card.sh <rootfs.tar.gz> <img|/dev/sdX> [sizeGiB]}"
target="${2:?usage}"; size_gib="${3:-12}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"
cleanup(){ [ -n "${m:-}" ] && umount -f "$m" 2>/dev/null || true; [ -n "${loop:-}" ] && losetup -d "$loop" 2>/dev/null || true; }
trap cleanup EXIT
if [ -b "$target" ]; then loop="$target"; else truncate -s "${size_gib}G" "$target"; loop="$(losetup --find --show "$target")"; fi
sfdisk --quiet "$loop" <<'SFD'
label: dos
start=8192, size=1048576, type=83
start=1064960, type=83
SFD
p1="${loop}p1"; p2="${loop}p2"; [ -e "$p1" ] || { p1="${loop}1"; p2="${loop}2"; }
mkfs.ext4 -q -F -L uke_root -U "$root_uuid" "$p2"
m="$(mktemp -d)"; mount "$p2" "$m"; tar xzf "$rootfs_tar" -C "$m"; umount "$m"; rmdir "$m"
echo "готово: $target (root UUID $root_uuid)"
