#!/usr/bin/env bash
# Build the working uke boot bundle: boot, init_boot, and custom stock-derived DTBO.
# Leave stock vendor_boot and vbmeta untouched.
# Usage: build-bundle-ztsubaki.sh --kernel F --init-boot F --dtbo F --cmdline F --out DIR
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
boot_size=100663296
init_boot_size=8388608

while [ $# -gt 0 ]; do
	case "$1" in
	--kernel)
		kernel="$2"
		shift 2
		;;
	--init-boot)
		init_boot="$2"
		shift 2
		;;
	--dtbo)
		dtbo="$2"
		shift 2
		;;
	--cmdline)
		cmdline_file="$2"
		shift 2
		;;
	--out)
		out="$2"
		shift 2
		;;
	*)
		echo "unknown argument: $1" >&2
		exit 1
		;;
	esac
done

for f in "${kernel:-}" "${init_boot:-}" "${dtbo:-}" "${cmdline_file:-}"; do
	[ -f "$f" ] || {
		echo "missing input: $f" >&2
		exit 1
	}
done

mkdir -p "$out"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

add_hash_footer() {
	local image="$1" partition="$2" size="$3" salt
	salt="$(sha256sum "$image" | cut -d' ' -f1)"
	python3 "$repo_root/tools/avbtool" add_hash_footer --image "$image" \
		--partition_name "$partition" --partition_size "$size" --salt "$salt"
}

cmdline="$(tr '\n' ' ' <"$cmdline_file" | sed 's/[[:space:]]*$//')"
python3 "$repo_root/tools/mkbootimg.py" --kernel "$kernel" --cmdline "$cmdline" \
	--header_version 4 --os_version 16.0.0 --os_patch_level 2026-01 \
	-o "$out/boot.img"
add_hash_footer "$out/boot.img" boot "$boot_size"

python3 "$repo_root/tools/mkbootimg.py" --ramdisk "$init_boot" \
	--header_version 4 --os_version 16.0.0 --os_patch_level 2026-01 \
	-o "$out/init_boot.img"
add_hash_footer "$out/init_boot.img" init_boot "$init_boot_size"

dtbo_src="$(readlink -f "$dtbo")"
dtbo_dst="$(readlink -m "$out/dtbo.img")"
[ "$dtbo_src" = "$dtbo_dst" ] || cp "$dtbo_src" "$dtbo_dst"
mkdtboimg dump "$out/dtbo.img" -b "$tmp/dtbo" >/dev/null

for spec in "boot.img:$boot_size" "init_boot.img:$init_boot_size"; do
	name="${spec%%:*}"
	expected="${spec##*:}"
	actual="$(stat -c %s "$out/$name")"
	[ "$actual" -eq "$expected" ] || {
		echo "$name: expected $expected bytes, got $actual" >&2
		exit 1
	}
done

(cd "$out" && sha256sum boot.img init_boot.img dtbo.img >SHA256SUMS)
echo "uke bundle: $out (boot.img + init_boot.img + dtbo.img)"
