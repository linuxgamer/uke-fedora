#!/usr/bin/env bash
# Полный бэкап планшета uke (crDroid + root) перед портом pmOS.
# Сохраняет: /sdcard, /data (приложения+настройки, без media/кэшей),
# ключевые разделы (boot/init_boot/vendor_boot/dtbo/vbmeta/persist).
#
# Использование: etc/tools/backup-device.sh [каталог]
set -euo pipefail

OUT="${1:-$HOME/uke-backup}"
mkdir -p "$OUT"

echo "== ждём устройство =="
adb wait-for-device

if ! adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	echo "Пробую adb root..."
	adb root 2>/dev/null || true
	sleep 2
fi
if ! adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	echo "ВНИМАНИЕ: нет root через adb. Дальше потребуется 'su' на устройстве."
fi

echo "== информация =="
adb shell getprop >"$OUT/getprop.txt" 2>/dev/null || true
adb shell 'cat /proc/partitions' >"$OUT/partitions.txt" 2>/dev/null || true
adb shell 'ls -l /dev/block/by-name' >"$OUT/by-name.txt" 2>/dev/null || true

# Обёртка: выполнить под root (adb root уже даёт uid=0, иначе su -c).
run_root() {
	if adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
		adb exec-out "$@"
	else
		adb exec-out su -c "$*"
	fi
}

echo "== /sdcard =="
adb pull /sdcard/ "$OUT/sdcard/" || echo "  (частично)"

echo "== /data (без media, cache) =="
# stderr удалённого tar подавляем, иначе adb подмешивает его в stdout и портит архив.
if adb shell 'id' 2>/dev/null | grep -q 'uid=0'; then
	adb exec-out sh -c 'tar -C /data -cf - --exclude=./media --exclude=./cache --exclude=./app-cache . 2>/dev/null' \
		>"$OUT/data.tar" || echo "  (ошибка tar)"
else
	adb exec-out su -c 'tar -C /data -cf - --exclude=./media --exclude=./cache --exclude=./app-cache . 2>/dev/null' \
		>"$OUT/data.tar" || echo "  (ошибка tar)"
fi

echo "== разделы =="
for p in boot_a init_boot_a vendor_boot_a dtbo_a vbmeta_a vbmeta_system_a persist; do
	echo "  $p"
	run_root dd if="/dev/block/by-name/$p" bs=4096 2>/dev/null >"$OUT/$p.img" ||
		echo "    пропущен"
done

echo "== размеры =="
du -sh "$OUT"/* 2>/dev/null | sort -h

echo
echo "Готово: $OUT"
echo "Сохрани каталог в надёжное место (вне планшета)."
