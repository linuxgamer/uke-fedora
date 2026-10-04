#!/bin/bash
# Установить Fedora rootfs на Xiaomi Pad 7 (uke) во ВНУТРЕННЮЮ память (userdata).
#
# *** УНИЧТОЖАЕТ ДАННЫЕ ANDROID *** (userdata переформатируется в ext4).
# Boot-цепочка (boot/init_boot/vendor_boot/dtbo) не трогается.
#
# Запуск с ПК, планшет в TWRP (adb):
#   ./rootfs/mk-internal-storage.sh <rootfs.tar.gz>
#
# UUID должен совпадать с boot/cmdline.txt (root=UUID=...).
set -euo pipefail

rootfs_tar="${1:?usage: mk-internal-storage.sh <rootfs.tar.gz> (планшет в TWRP)}"
[ -f "$rootfs_tar" ] || {
	echo "нет $rootfs_tar" >&2
	exit 1
}

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(dirname "$script_dir")"
assets="$repo_dir/local-assets"
kver="${UKE_KERNEL_VERSION:-7.2.0-rc2-uke}"
user="${UKE_USER:-fedora}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"

command -v adb >/dev/null || {
	echo "adb не установлен" >&2
	exit 1
}
state="$(adb get-state 2>/dev/null || true)"
[ "$state" = "recovery" ] || {
	echo "планшет не в recovery (adb: '${state:-none}')" >&2
	exit 1
}

device="$(adb shell getprop ro.product.device | tr -d '\r')"
case "$device" in
uke) ;;
*)
	echo "ОТКАЗ: ожидался device uke, получен '$device'" >&2
	exit 1
	;;
esac

part="/dev/block/by-name/userdata"
size="$(adb shell "blockdev --getsize64 $part" | tr -d '\r')"
[ "${size:-0}" -gt $((30 * 1024 * 1024 * 1024)) ] 2>/dev/null || {
	echo "ОТКАЗ: userdata ${size:-?} байт — не тот раздел?" >&2
	exit 1
}

printf '\n%s\n' "****************************************************************************"
printf '%s\n' "  ВНИМАНИЕ: userdata (~$((size / 1024 / 1024 / 1024)) GB) будет ОТФОРМАТИРОВАНА"
printf '%s\n' "  Данные Android будут УНИЧТОЖЕНЫ. Откат: стоковая прошивка / TWRP Format Data."
printf '%s\n\n' "****************************************************************************" >&2
[ -t 0 ] || {
	echo "ОТКАЗ: нет TTY для подтверждения" >&2
	exit 1
}
read -r -p "Введи DESTROY для форматирования userdata: " ans
[ "$ans" = "DESTROY" ] || {
	echo "отменено" >&2
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
# -F дважды: mke2fs форсит даже если устройство смонтировано (TWRP держит /data)
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
echo ">>> установка rootfs завершена"
'
echo ">>> готово. TWRP -> Reboot -> System; ssh ${user}@172.16.42.1"
