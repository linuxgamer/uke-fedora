#!/usr/bin/env bash
# Full backup of an uke tablet (crDroid with root) before porting work.
# Saves /sdcard, /data (applications and settings, excluding media/cache), and
# key partitions (boot/init_boot/vendor_boot/dtbo/vbmeta/persist).
#
# Usage: tools/backup-device.sh [directory]
set -euo pipefail

OUT="${1:-$HOME/uke-backup}"
mkdir -p "$OUT"

echo "== waiting for device =="
adb wait-for-device

if ! adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	echo "Trying adb root..."
	adb root 2>/dev/null || true
	sleep 2
fi
if ! adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	echo "WARNING: adb root is unavailable. The device must provide 'su'."
fi

echo "== device information =="
adb shell getprop >"$OUT/getprop.txt" 2>/dev/null || true
adb shell 'cat /proc/partitions' >"$OUT/partitions.txt" 2>/dev/null || true
adb shell 'ls -l /dev/block/by-name' >"$OUT/by-name.txt" 2>/dev/null || true

# Wrapper: run as root (adb root has uid=0; otherwise use su -c).
run_root() {
	if adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
		adb exec-out "$@"
	else
		adb exec-out su -c "$*"
	fi
}

echo "== /sdcard =="
adb pull /sdcard/ "$OUT/sdcard/" || echo "  (partial)"

echo "== /data (excluding media and cache) =="
# Suppress remote tar stderr so adb cannot mix it into stdout and corrupt the archive.
if adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	adb exec-out sh -c 'tar -C /data -cf - --exclude=./media --exclude=./cache --exclude=./app-cache . 2>/dev/null' \
		>"$OUT/data.tar" || echo "  (tar failed)"
else
	adb exec-out su -c 'tar -C /data -cf - --exclude=./media --exclude=./cache --exclude=./app-cache . 2>/dev/null' \
		>"$OUT/data.tar" || echo "  (tar failed)"
fi

echo "== partitions =="
# Exact uke GPT partition sizes; dd reads a few bytes past the block device, so
# truncate the result to the partition size.
declare -A PART_SIZE=(
	[boot_a]=100663296 [init_boot_a]=8388608 [vendor_boot_a]=100663296
	[dtbo_a]=25165824 [vbmeta_a]=131072 [vbmeta_system_a]=131072 [persist]=33554432
)
for p in boot_a init_boot_a vendor_boot_a dtbo_a vbmeta_a vbmeta_system_a persist; do
	echo "  $p"
	run_root dd if="/dev/block/by-name/$p" bs=4096 2>/dev/null >"$OUT/$p.img" ||
		{
			echo "    skipped"
			continue
		}
	[ -n "${PART_SIZE[$p]:-}" ] && truncate -s "${PART_SIZE[$p]}" "$OUT/$p.img"
done

echo "== sizes =="
du -sh "$OUT"/* 2>/dev/null | sort -h

echo
echo "Complete: $OUT"
echo "Store this directory somewhere safe, outside the tablet."
