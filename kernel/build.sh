#!/usr/bin/env bash
# Build the pinned, patched Uke kernel and install its modules for the rootfs.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="${KERNEL_SOURCE_DIR:-$root/build/ztsubaki/linux}"
out="${KERNEL_OUT:-$root/build/ztsubaki/out}"
modules_root="${MODULES_ROOT:-$root/build/ztsubaki/modules}"
config="$root/kernel/configs/uke.config"
jobs="${JOBS:-$(nproc)}"

[ -d "$source_root" ] || {
	echo "missing kernel source: run kernel/prepare.sh first" >&2
	exit 1
}

mkdir -p "$out"
cp "$config" "$out/.config"
make -C "$source_root" O="$out" ARCH=arm64 LLVM=1 olddefconfig
make -C "$source_root" O="$out" ARCH=arm64 LLVM=1 -j"$jobs" Image.gz modules
rm -rf "$modules_root/usr/lib/modules"
make -C "$source_root" O="$out" ARCH=arm64 LLVM=1 \
	INSTALL_MOD_PATH="$modules_root/usr" modules_install

kernel_release="$(make -s -C "$source_root" O="$out" ARCH=arm64 kernelrelease)"
[ "$kernel_release" = "6.12.0-dirty" ] || {
	echo "unexpected kernel release: $kernel_release" >&2
	exit 1
}
echo "kernel output: $out"
echo "modules: $modules_root/usr/lib/modules/$kernel_release"
