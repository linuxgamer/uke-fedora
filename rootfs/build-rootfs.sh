#!/bin/bash
# Build a Fedora aarch64 rootfs for uke.
#
# Two modes:
#  1) In an arm64 Fedora container (native):
#     docker run --rm --network host -v "$PWD:/work" -w /work \
#         quay.io/fedora/fedora:44 ./rootfs/build-rootfs.sh
#  2) Host-native on x86_64 (faster than emulation; x86_64 dnf, qemu scriptlets):
#     sudo DNF_FORCEARCH=aarch64 DNF_REPOSDIR="$PWD/rootfs/fedora-repos" ./rootfs/build-rootfs.sh
set -euo pipefail

fedora_release="${FEDORA_RELEASE:-44}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(dirname "$script_dir")"
rootfs="${ROOTFS_DIR:-$repo_root/build/fedora-rootfs}"
outdir="${OUT_DIR:-$repo_root/build/fedora}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"
kver="${UKE_KERNEL_VERSION:-6.12.0-dirty}"
modules_src="${MODULES_SRC:-$repo_root/build/ztsubaki/modules/usr/lib/modules/$kver}"
firmware_tar="${FIRMWARE_TARBALL:-$repo_root/rootfs/firmware.tar.gz}"
user="${UKE_USER:-fedora}"

DNF_ARGS=(--installroot="$rootfs" --releasever="$fedora_release"
	--setopt=install_weak_deps=False --setopt=tsflags=nodocs)
[ -n "${DNF_USE_HOST_CONFIG:-}" ] && DNF_ARGS+=(--use-host-config)
[ -n "${DNF_FORCEARCH:-}" ] && DNF_ARGS+=(--forcearch="$DNF_FORCEARCH")
[ -n "${DNF_REPOSDIR:-}" ] && DNF_ARGS+=(--setopt=reposdir="$DNF_REPOSDIR")

echo ">>> Fedora $fedora_release rootfs for uke (KVER $kver)"
mkdir -p "$rootfs" "$outdir"

echo ">>> @core packages"
dnf -y "${DNF_ARGS[@]}" install \
	@core \
	NetworkManager openssh-server openssh-clients \
	sudo chrony zram-generator python3 \
	alsa-ucm alsa-utils dtc kmod e2fsprogs \
	qcom-firmware atheros-firmware

echo ">>> Overlay"
cp -a "$script_dir/overlay/." "$rootfs/"

echo ">>> fstab / hostname / SELinux"
printf "UUID=%s / ext4 defaults 0 0\n" "$root_uuid" >"$rootfs/etc/fstab"
echo "uke-fedora" >"$rootfs/etc/hostname"
[ -f "$rootfs/etc/selinux/config" ] && sed -i 's/^SELINUX=.*/SELINUX=permissive/' "$rootfs/etc/selinux/config" || true

echo ">>> Kernel modules"
if [ -d "$modules_src" ]; then
	mkdir -p "$rootfs/usr/lib/modules"
	cp -a "$modules_src" "$rootfs/usr/lib/modules/"
	depmod -b "$rootfs" "$kver" 2>/dev/null || true
else
	echo "    WARN: missing $modules_src" >&2
fi

echo ">>> Firmware"
[ -f "$firmware_tar" ] && tar xzf "$firmware_tar" -C "$rootfs/usr" 2>/dev/null ||
	echo "    WARN: missing $firmware_tar" >&2

echo ">>> USB gadget net"
mkdir -p "$rootfs/etc/NetworkManager/system-connections"
cat >"$rootfs/etc/NetworkManager/system-connections/usb0.nmconnection" <<'NM'
[connection]
id=usb0
interface-name=usb0
type=ethernet
autoconnect=true
[ipv4]
address1=172.16.42.1/24
method=manual
[ipv6]
method=disabled
NM
chmod 600 "$rootfs/etc/NetworkManager/system-connections/usb0.nmconnection"

echo ">>> User ${user}"
if ! chroot "$rootfs" /usr/bin/id "$user" >/dev/null 2>&1; then
	chroot "$rootfs" /usr/sbin/useradd -m -G wheel -s /bin/bash "$user" || true
	echo "${user}:${user}" | chroot "$rootfs" /usr/bin/chpasswd || true
fi

echo ">>> Set root ownership"
chroot "$rootfs" /bin/sh -c 'chown -R root:root / 2>/dev/null' || true

echo ">>> Packaging"
tar -C "$rootfs" -czf "$outdir/uke-fedora-rootfs.tar.gz" .
ls -la "$outdir/uke-fedora-rootfs.tar.gz"
