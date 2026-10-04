#!/usr/bin/env bash
# Собрать ext4-образ rootfs uke и прошить в userdata через fastboot.
# Обходит TWRP/dm-проблему (dm-7 держит userdata).
#   ./rootfs/mk-internal-storage-fastboot.sh [size-GiB]   (по умолчанию 8)
# Затем: fastboot flash userdata build/fedora/uke-rootfs.sparse.img
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rootfs_tar="${ROOTFS_TAR:-$ROOT/build/fedora/uke-fedora-rootfs.tar.gz}"
size_gib="${1:-8}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"
img="$ROOT/build/fedora/uke-rootfs.img"
sparse="$ROOT/build/fedora/uke-rootfs.sparse.img"

[ -f "$rootfs_tar" ] || { echo "нет $rootfs_tar" >&2; exit 1; }
mkdir -p "$(dirname "$img")"

echo ">>> ext4-образ ${size_gib}G, метка uke_root, UUID $root_uuid"
rm -f "$img" "$sparse"
truncate -s "${size_gib}G" "$img"
mke2fs -F -t ext4 -L uke_root -U "$root_uuid" -m 1 "$img" >/dev/null

mnt="$(mktemp -d)"
sudo mount -o loop "$img" "$mnt"
sudo tar xzf "$rootfs_tar" -C "$mnt"
printf "UUID=%s / ext4 defaults 0 0\n" "$root_uuid" | sudo tee "$mnt/etc/fstab" >/dev/null
sudo mkdir -p "$mnt"/proc "$mnt"/sys "$mnt"/dev "$mnt"/run "$mnt"/tmp "$mnt"/boot
sudo chmod 1777 "$mnt/tmp"
sudo umount "$mnt"
rmdir "$mnt"
e2fsck -fy "$img" >/dev/null 2>&1 || true

echo ">>> sparse-образ"
img2simg "$img" "$sparse"
rm -f "$img"
ls -la "$sparse"
echo
echo "Прошей:  fastboot flash userdata $sparse"
