#!/usr/bin/env bash
# Create the complete patched kernel source archive required with binary releases.
set -euo pipefail

while [ $# -gt 0 ]; do
	case "$1" in
	--out)
		out="$2"
		shift 2
		;;
	*)
		echo "usage: package-source.sh --out DIR" >&2
		exit 1
		;;
	esac
done

[ -n "${out:-}" ] || {
	echo "usage: package-source.sh --out DIR" >&2
	exit 1
}

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
upstream_url="https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
upstream_ref="v6.12"
upstream_commit="adc218676eef25575469234709c2d87185ca223a"
tmp="$(mktemp -d)"
source_root="$tmp/linux-6.12-uke"
trap 'rm -rf "$tmp"' EXIT

git clone --depth 1 --branch "$upstream_ref" "$upstream_url" "$source_root"
[ "$(git -C "$source_root" rev-parse HEAD)" = "$upstream_commit" ] || {
	echo "unexpected upstream commit" >&2
	exit 1
}

while IFS= read -r patch || [ -n "$patch" ]; do
	case "$patch" in
	'' | '#'*) continue ;;
	esac
	git -C "$source_root" apply "$root/kernel/patches/uke/$patch"
done <"$root/kernel/patches/uke/series"

cp "$root/kernel/configs/uke.config" "$source_root/UKE-CONFIG"
cp "$root/kernel/modules.load" "$source_root/UKE-MODULES-LOAD"
printf '%s\n' -dirty >"$source_root/localversion-uke"
cp "$root/kernel/SOURCE-MANIFEST" "$source_root/UKE-SOURCE-MANIFEST"
mkdir -p "$out"
tar --zstd --sort=name --owner=0 --group=0 --numeric-owner --exclude=.git \
	-cf "$out/linux-6.12-uke-source.tar.zst" -C "$tmp" linux-6.12-uke
sha256sum "$out/linux-6.12-uke-source.tar.zst" >"$out/linux-6.12-uke-source.tar.zst.sha256"
echo "kernel source archive: $out/linux-6.12-uke-source.tar.zst"
