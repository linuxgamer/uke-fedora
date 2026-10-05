#!/bin/bash
# Build an Android boot image v4 bundle for uke (Xiaomi Pad 7).
# Adapted from gts9wifi-fedora (nacht20-de); its layout is verified there:
#   - boot: kernel (Image.gz) + appended DTB, empty ABL command line
#   - init_boot: empty generic ramdisk in legacy LZ4 (8 MiB partition)
#   - vendor_boot: full initramfs (platform fragment) + DTB + cmdline + bootconfig
#   - dtbo: not a DT table (zero page), so ABL selects the appended DTB
#   - vbmeta: verification disabled (flags 2), hash footers for all images
#
# Usage: build-bundle.sh --image Image --dtb F --initramfs F \
#                        --cmdline F --bootconfig F --out DIR
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

# uke partition sizes from stock firmware.
boot_size=100663296        # 96 MiB
init_boot_size=8388608     # 8 MiB
vendor_boot_size=100663296 # 96 MiB
dtbo_size=25165824         # 24 MiB
vbmeta_size=131072         # 128 KiB

while [ $# -gt 0 ]; do
	case "$1" in
	--vmlinuz)
		vmlinuz="$2"
		shift 2
		;;
	--dtb)
		dtb="$2"
		shift 2
		;;
	--initramfs)
		initramfs="$2"
		shift 2
		;;
	--cmdline)
		cmdline_file="$2"
		shift 2
		;;
	--bootconfig)
		bootconfig="$2"
		shift 2
		;;
	--out)
		out="$2"
		shift 2
		;;
	*)
		echo "unknown arg: $1" >&2
		exit 1
		;;
	esac
done

for f in "$vmlinuz" "$dtb" "$initramfs" "$cmdline_file" "$bootconfig"; do
	[ -f "$f" ] || {
		echo "missing input: $f" >&2
		exit 1
	}
done
for f in "$repo_root/tools/mkbootimg.py" "$repo_root/tools/avbtool"; do
	[ -f "$f" ] || {
		echo "missing tool: $f" >&2
		exit 1
	}
done
command -v lz4 >/dev/null || {
	echo "lz4 not installed" >&2
	exit 1
}

mkdir -p "$out"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

add_hash_footer() {
	local target="$1" partition="$2" partition_size="$3" salt
	salt=$(sha256sum "$target" | cut -d' ' -f1)
	python3 "$repo_root/tools/avbtool" add_hash_footer \
		--image "$target" --partition_name "$partition" \
		--partition_size "$partition_size" --salt "$salt"
}

# Fedora vmlinuz.efi is EFI zboot; ABL needs the raw compressed payload.
python3 "$repo_root/boot/extract-zboot-payload.py" "$vmlinuz" "$tmp/Image.gz"

# init_boot: empty generic cpio in legacy LZ4.
mkdir -p "$tmp/empty-ramdisk"
touch -d '@0' "$tmp/empty-ramdisk"
(
	cd "$tmp/empty-ramdisk"
	find . -print0 | cpio --reproducible --null -o --format=newc 2>/dev/null
) | lz4 -l -12 - "$tmp/empty.lz4" >/dev/null

# Full initramfs (dracut, gzip) -> legacy LZ4 for vendor_boot.
gzip -t "$initramfs"
full_ramdisk="$tmp/initramfs.lz4"
gzip -dc "$initramfs" | lz4 -l -12 - "$full_ramdisk" >/dev/null

cmdline=$(tr '\n' ' ' <"$cmdline_file" | sed 's/[[:space:]]*$//')

# boot: kernel plus appended DTB, empty command line.
cat "$tmp/Image.gz" "$dtb" >"$tmp/Image.gz-dtb"
python3 "$repo_root/tools/mkbootimg.py" \
	--kernel "$tmp/Image.gz-dtb" --cmdline '' \
	--header_version 4 --os_version 16 --os_patch_level 2026-01 \
	-o "$out/boot.img"
add_hash_footer "$out/boot.img" boot "$boot_size"

# init_boot: empty ramdisk.
python3 "$repo_root/tools/mkbootimg.py" \
	--ramdisk "$tmp/empty.lz4" --header_version 4 \
	-o "$out/init_boot.img"
add_hash_footer "$out/init_boot.img" init_boot "$init_boot_size"

# vendor_boot: full initramfs plus DTB, cmdline, and bootconfig.
python3 "$repo_root/tools/mkbootimg.py" \
	--ramdisk_type platform --ramdisk_name '' \
	--vendor_ramdisk_fragment "$full_ramdisk" \
	--dtb "$dtb" --vendor_cmdline "$cmdline" \
	--header_version 4 --vendor_boot "$out/vendor_boot.img" \
	--base 0x80000000 --kernel_offset 0x8000 \
	--ramdisk_offset 0x02000000 --tags_offset 0x01e00000 \
	--pagesize 4096 --dtb_offset 0x1f00000 \
	--vendor_bootconfig "$bootconfig"
add_hash_footer "$out/vendor_boot.img" vendor_boot "$vendor_boot_size"

# dtbo: zero page, not a DT table.
rm -f "$out/dtbo.img"
truncate -s 4096 "$out/dtbo.img"
add_hash_footer "$out/dtbo.img" dtbo "$dtbo_size"

# vbmeta: disable verified boot.
python3 "$repo_root/tools/avbtool" make_vbmeta_image \
	--output "$out/vbmeta.img" --flags 2 --padding_size "$vbmeta_size"

for spec in "boot.img:$boot_size" "init_boot.img:$init_boot_size" \
	"vendor_boot.img:$vendor_boot_size" "dtbo.img:$dtbo_size" \
	"vbmeta.img:$vbmeta_size"; do
	name=${spec%%:*}
	expected=${spec##*:}
	actual=$(stat -c %s "$out/$name")
	[ "$actual" -eq "$expected" ] || {
		echo "$name: expected $expected, got $actual" >&2
		exit 1
	}
done

(cd "$out" && sha256sum *.img >SHA256SUMS)
echo "bundle ready: $out"
