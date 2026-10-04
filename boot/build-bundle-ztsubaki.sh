#!/bin/bash
# Собрать ztsubaki-схему для uke: ТОЛЬКО boot + init_boot.
# Стоковые vendor_boot/dtbo/vbmeta НЕ трогаем (Xiaomi ABL их не принимает).
#   boot:      Image.gz + appended DTB + наш cmdline
#   init_boot: минимальный busybox-initramfs (lz4)
# Usage: build-bundle-ztsubaki.sh --vmlinuz F --dtb F --init-boot F \
#                                 --cmdline F --out DIR
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
boot_size=100663296
init_boot_size=8388608

while [ $# -gt 0 ]; do
    case "$1" in
        --vmlinuz) vmlinuz="$2"; shift 2 ;;
        --dtb) dtb="$2"; shift 2 ;;
        --init-boot) init_boot="$2"; shift 2 ;;
        --cmdline) cmdline_file="$2"; shift 2 ;;
        --out) out="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done
for f in "$vmlinuz" "$dtb" "$init_boot" "$cmdline_file"; do
    [ -f "$f" ] || { echo "missing input: $f" >&2; exit 1; }
done
mkdir -p "$out"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

add_hash_footer() {
    local t="$1" p="$2" s="$3" salt
    salt=$(sha256sum "$t" | cut -d' ' -f1)
    python3 "$repo_root/tools/avbtool" add_hash_footer --image "$t" \
        --partition_name "$p" --partition_size "$s" --salt "$salt"
}

# payload из EFI zboot
python3 "$repo_root/boot/extract-zboot-payload.py" "$vmlinuz" "$tmp/Image.gz"
cat "$tmp/Image.gz" "$dtb" > "$tmp/Image.gz-dtb"
cmdline=$(tr '\n' ' ' < "$cmdline_file" | sed 's/[[:space:]]*$//')

python3 "$repo_root/tools/mkbootimg.py" --kernel "$tmp/Image.gz-dtb" \
    --cmdline "$cmdline" --header_version 4 --os_version 16 --os_patch_level 2026-01 \
    -o "$out/boot.img"
add_hash_footer "$out/boot.img" boot "$boot_size"

python3 "$repo_root/tools/mkbootimg.py" --ramdisk "$init_boot" \
    --header_version 4 -o "$out/init_boot.img"
add_hash_footer "$out/init_boot.img" init_boot "$init_boot_size"

for spec in "boot.img:$boot_size" "init_boot.img:$init_boot_size"; do
    n=${spec%%:*}; e=${spec##*:}; a=$(stat -c %s "$out/$n")
    [ "$a" -eq "$e" ] || { echo "$n: expected $e got $a" >&2; exit 1; }
done
(cd "$out" && sha256sum *.img > SHA256SUMS)
echo "ztsubaki bundle: $out (boot.img + init_boot.img)"
