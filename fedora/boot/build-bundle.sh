#!/bin/bash
# Собрать Android boot-image-v4 бандл для uke (Xiaomi Pad 7).
# Адаптировано из gts9wifi-fedora (nacht20-de), логика проверена на железе там:
#   - boot: kernel (Image.gz) + appended DTB, пустой cmdline (ABL)
#   - init_boot: пустой generic ramdisk в legacy LZ4 (init_boot = 8 МиБ)
#   - vendor_boot: полный initramfs (platform fragment) + DTB + cmdline + bootconfig
#   - dtbo: НЕ таблица DT (нулевая страница) -> ABL берёт appended DTB
#   - vbmeta: verification disabled (flags 2), hash footers на всё
#
# Usage: build-bundle.sh --image Image --dtb F --initramfs F \
#                        --cmdline F --bootconfig F --out DIR
set -euo pipefail

fedora_root="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(dirname "$fedora_root")"

# Размеры разделов uke (из стока; уточнить на железе при необходимости).
boot_size=100663296       # 96 МиБ
init_boot_size=8388608    # 8 МиБ
vendor_boot_size=100663296 # 96 МиБ
dtbo_size=25165824        # 24 МиБ
vbmeta_size=131072        # 128 КиБ

while [ $# -gt 0 ]; do
    case "$1" in
        --image) image_in="$2"; shift 2 ;;
        --dtb) dtb="$2"; shift 2 ;;
        --initramfs) initramfs="$2"; shift 2 ;;
        --cmdline) cmdline_file="$2"; shift 2 ;;
        --bootconfig) bootconfig="$2"; shift 2 ;;
        --out) out="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

for f in "$image_in" "$dtb" "$initramfs" "$cmdline_file" "$bootconfig"; do
    [ -f "$f" ] || { echo "missing input: $f" >&2; exit 1; }
done
for f in "$fedora_root/tools/mkbootimg.py" "$fedora_root/tools/avbtool"; do
    [ -f "$f" ] || { echo "missing tool: $f" >&2; exit 1; }
done
command -v lz4 >/dev/null || { echo "lz4 not installed" >&2; exit 1; }

mkdir -p "$out"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

add_hash_footer() {
    local target="$1" partition="$2" partition_size="$3" salt
    salt=$(sha256sum "$target" | cut -d' ' -f1)
    python3 "$fedora_root/tools/avbtool" add_hash_footer \
        --image "$target" --partition_name "$partition" \
        --partition_size "$partition_size" --salt "$salt"
}

# Наш Image — несжатый; ABL ждёт сжатый kernel.
gzip -9 -c "$image_in" > "$tmp/Image.gz"

# init_boot: пустой generic cpio в legacy LZ4.
mkdir -p "$tmp/empty-ramdisk"
touch -d '@0' "$tmp/empty-ramdisk"
(
    cd "$tmp/empty-ramdisk"
    find . -print0 | cpio --reproducible --null -o --format=newc 2>/dev/null
) | lz4 -l -12 - "$tmp/empty.lz4" >/dev/null

# Полный initramfs (dracut, gzip) -> legacy LZ4 для vendor_boot.
gzip -t "$initramfs"
full_ramdisk="$tmp/initramfs.lz4"
gzip -dc "$initramfs" | lz4 -l -12 - "$full_ramdisk" >/dev/null

cmdline=$(tr '\n' ' ' < "$cmdline_file" | sed 's/[[:space:]]*$//')

# boot: kernel + appended DTB, пустой cmdline.
cat "$tmp/Image.gz" "$dtb" > "$tmp/Image.gz-dtb"
python3 "$fedora_root/tools/mkbootimg.py" \
    --kernel "$tmp/Image.gz-dtb" --cmdline '' \
    --header_version 4 --os_version 16 --os_patch_level 2026-01 \
    -o "$out/boot.img"
add_hash_footer "$out/boot.img" boot "$boot_size"

# init_boot: пустой ramdisk.
python3 "$fedora_root/tools/mkbootimg.py" \
    --ramdisk "$tmp/empty.lz4" --header_version 4 \
    -o "$out/init_boot.img"
add_hash_footer "$out/init_boot.img" init_boot "$init_boot_size"

# vendor_boot: полный initramfs + DTB + cmdline + bootconfig.
python3 "$fedora_root/tools/mkbootimg.py" \
    --ramdisk_type platform --ramdisk_name '' \
    --vendor_ramdisk_fragment "$full_ramdisk" \
    --dtb "$dtb" --vendor_cmdline "$cmdline" \
    --header_version 4 --vendor_boot "$out/vendor_boot.img" \
    --base 0x80000000 --kernel_offset 0x8000 \
    --ramdisk_offset 0x02000000 --tags_offset 0x01e00000 \
    --pagesize 4096 --dtb_offset 0x1f00000 \
    --vendor_bootconfig "$bootconfig"
add_hash_footer "$out/vendor_boot.img" vendor_boot "$vendor_boot_size"

# dtbo: нулевая страница (не таблица DT).
rm -f "$out/dtbo.img"
truncate -s 4096 "$out/dtbo.img"
add_hash_footer "$out/dtbo.img" dtbo "$dtbo_size"

# vbmeta: выключить verified boot.
python3 "$fedora_root/tools/avbtool" make_vbmeta_image \
    --output "$out/vbmeta.img" --flags 2 --padding_size "$vbmeta_size"

for spec in "boot.img:$boot_size" "init_boot.img:$init_boot_size" \
            "vendor_boot.img:$vendor_boot_size" "dtbo.img:$dtbo_size" \
            "vbmeta.img:$vbmeta_size"; do
    name=${spec%%:*}; expected=${spec##*:}
    actual=$(stat -c %s "$out/$name")
    [ "$actual" -eq "$expected" ] || { echo "$name: expected $expected, got $actual" >&2; exit 1; }
done

(cd "$out" && sha256sum *.img > SHA256SUMS)
echo "bundle ready: $out"
