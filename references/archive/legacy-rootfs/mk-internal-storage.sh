#!/bin/bash
# Install the Fedora rootfs to Xiaomi Pad 7 (`uke`) internal storage (`userdata`).
#
# *** DESTROYS ANDROID USER DATA *** (`userdata` is reformatted as ext4).
# The boot chain (`boot`/`init_boot`/`vendor_boot`/`dtbo`) is unchanged.
#
# Run from the host with the tablet in TWRP (adb):
#   ./rootfs/mk-internal-storage.sh <rootfs.tar.gz>
#
# The UUID must match `root=UUID=...` in the boot command line.
set -euo pipefail

rootfs_tar="${1:?usage: mk-internal-storage.sh <rootfs.tar.gz> (tablet in TWRP)}"
[ -f "$rootfs_tar" ] || {
	echo "missing $rootfs_tar" >&2
	exit 1
}

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(dirname "$script_dir")"
assets="$repo_dir/local-assets"
kver="${UKE_KERNEL_VERSION:-7.2.0-rc2-uke}"
user="${UKE_USER:-fedora}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"

command -v adb >/dev/null || {
	echo "adb is not installed" >&2
	exit 1
}
state="$(adb get-state 2>/dev/null || true)"
[ "$state" = "recovery" ] || {
	echo "tablet is not in recovery (adb: '${state:-none}')" >&2
	exit 1
}

device="$(adb shell getprop ro.product.device | tr -d '\r')"
case "$device" in
uke) ;;
*)
	echo "refusing: expected device uke, got '$device'" >&2
	exit 1
	;;
esac

part="/dev/block/by-name/userdata"
size="$(adb shell "blockdev --getsize64 $part" | tr -d '\r')"
[ "${size:-0}" -gt $((30 * 1024 * 1024 * 1024)) ] 2>/dev/null || {
	echo "refusing: userdata is ${size:-?} bytes; is this the wrong partition?" >&2
	exit 1
}

printf '\n%s\n' "****************************************************************************"
printf '%s\n' "  WARNING: userdata (~$((size / 1024 / 1024 / 1024)) GB) WILL BE REFORMATTED"
printf '%s\n' "  Android data will be destroyed. Recovery: stock firmware or TWRP Format Data."
printf '%s\n\n' "****************************************************************************" >&2
[ -t 0 ] || {
	echo "refusing: no TTY available for confirmation" >&2
	exit 1
}
read -r -p "Type DESTROY to format userdata: " ans
[ "$ans" = "DESTROY" ] || {
	echo "cancelled" >&2
	exit 1
}

adb push "$rootfs_tar" /tmp/uke-rootfs.tar.gz
[ -f "$assets/firmware.tar.gz" ] && adb push "$assets/firmware.tar.gz" /tmp/uke-firmware.tar.gz || true
if [ -d "$assets/modules/$kver" ]; then
	tar -C "$assets/modules" -czf /tmp/uke-modules.tar.gz "$kver"
	adb push /tmp/uke-modules.tar.gz /tmp/uke-modules.tar.gz
fi

adb shell '
set -e
DEV=/dev/block/by-name/userdata
for m in /sdcard /data; do
    umount -f "$m" 2>/dev/null || umount -l "$m" 2>/dev/null || true
done
umount -f "$DEV" 2>/dev/null || umount -l "$DEV" 2>/dev/null || true
# Two -F flags force mke2fs even when TWRP still holds /data mounted.
mke2fs -F -F -t ext4 -m 1 -U '"$root_uuid"' -L uke_root "$DEV"
mkdir -p /rmnt
mount -t ext4 "$DEV" /rmnt
tar xzf /tmp/uke-rootfs.tar.gz -C /rmnt
[ -f /tmp/uke-firmware.tar.gz ] && tar xzf /tmp/uke-firmware.tar.gz -C /rmnt || true
if [ -f /tmp/uke-modules.tar.gz ]; then
    mkdir -p /rmnt/usr/lib/modules
    tar xzf /tmp/uke-modules.tar.gz -C /rmnt/usr/lib/modules
fi
printf "UUID='"$root_uuid"' / ext4 defaults 0 0\n" > /rmnt/etc/fstab
mkdir -p /rmnt/proc /rmnt/sys /rmnt/dev /rmnt/run /rmnt/tmp /rmnt/boot
chmod 1777 /rmnt/tmp
rm -f /tmp/uke-rootfs.tar.gz /tmp/uke-firmware.tar.gz /tmp/uke-modules.tar.gz
sync
umount /rmnt
e2fsck -fy "$DEV"
echo ">>> rootfs installation complete"
'
echo ">>> complete. TWRP -> Reboot -> System; ssh ${user}@172.16.42.1"
