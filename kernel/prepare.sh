#!/usr/bin/env bash
# Fetch the pinned upstream kernel and apply the tracked Uke patch series.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="${KERNEL_SOURCE_DIR:-$root/build/ztsubaki/linux}"
upstream_url="https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
upstream_ref="v6.12"
upstream_commit="adc218676eef25575469234709c2d87185ca223a"

[ ! -e "$source_root" ] || {
	echo "refusing to overwrite existing kernel source: $source_root" >&2
	exit 1
}

mkdir -p "$(dirname "$source_root")"
git clone --depth 1 --branch "$upstream_ref" "$upstream_url" "$source_root"
[ "$(git -C "$source_root" rev-parse HEAD)" = "$upstream_commit" ] || {
	echo "unexpected upstream commit" >&2
	exit 1
}

while IFS= read -r patch || [ -n "$patch" ]; do
	case "$patch" in
	'' | '#'*) continue ;;
	esac
	patch_file="$root/kernel/patches/uke/$patch"
	[ -f "$patch_file" ] || {
		echo "missing patch: $patch_file" >&2
		exit 1
	}
	git -C "$source_root" apply --check "$patch_file"
	git -C "$source_root" apply "$patch_file"
done <"$root/kernel/patches/uke/series"

echo "prepared kernel source: $source_root"
