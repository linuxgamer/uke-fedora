#!/usr/bin/env bash
# Package validated boot images and a raw rootfs for a GitHub release.
# Usage: package-release.sh --bundle DIR --rootfs F --out DIR
set -euo pipefail

while [ $# -gt 0 ]; do
	case "$1" in
	--bundle)
		bundle="$2"
		shift 2
		;;
	--rootfs)
		rootfs="$2"
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

for image in boot.img init_boot.img dtbo.img; do
	[ -f "${bundle:-}/$image" ] || {
		echo "missing bundle image: ${bundle:-}/$image" >&2
		exit 1
	}
done
[ -f "${rootfs:-}" ] || {
	echo "missing rootfs image: ${rootfs:-}" >&2
	exit 1
}
[ -n "${out:-}" ] || {
	echo "missing --out" >&2
	exit 1
}

for tool in zstd sha256sum mkdtboimg fdtget; do
	command -v "$tool" >/dev/null || {
		echo "missing required tool: $tool" >&2
		exit 1
	}
done

mkdir -p "$out"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "${bundle}/boot.img" "${bundle}/init_boot.img" "${bundle}/dtbo.img" "$out/"
mkdtboimg dump "$out/dtbo.img" -b "$tmp/dtbo" >/dev/null
fdtget -t s "$tmp/dtbo.0" /fragment@134/__overlay__ compatible | grep -qx 'qcom,sm8550-ufshc qcom,ufshc'
zstd -T0 -19 -f "$rootfs" -o "$out/uke-rootfs.img.zst"

(cd "$out" && sha256sum boot.img init_boot.img dtbo.img uke-rootfs.img.zst >SHA256SUMS)
sha256sum "$rootfs" | sed 's#  .*#  uke-rootfs.img#' >"$out/uke-rootfs.img.sha256"
zstd -t "$out/uke-rootfs.img.zst"
(cd "$out" && sha256sum -c SHA256SUMS)
echo "release bundle: $out"
