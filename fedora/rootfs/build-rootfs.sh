#!/bin/bash
# Собрать минимальный Fedora aarch64 rootfs для uke (Xiaomi Pad 7).
# Запускать ВНУТРИ aarch64 Fedora-контейнера (docker/podman --platform linux/arm64):
#   docker run --rm --network host -v "$PWD:/work" -w /work \
#       quay.io/fedora/fedora:44 ./fedora/rootfs/build-rootfs.sh
#
# Первый bring-up: @core + systemd, без графики. GNOME добавим после загрузки.
set -euo pipefail

fedora_release="${FEDORA_RELEASE:-44}"
rootfs="${ROOTFS_DIR:-/work/build/fedora-rootfs}"
outdir="${OUT_DIR:-/work/build/fedora}"
root_uuid="${ROOT_UUID:-19364720-0ee1-4715-b30a-51a47d4a814c}"
# Каталог с модулями ядра (usr/lib/modules/<kver>) и firmware.tar.gz.
modules_src="${MODULES_SRC:-/work/build/uke-modules}"
firmware_tar="${FIRMWARE_TARBALL:-/work/pmos/firmware-xiaomi-uke/firmware.tar.gz}"

script_dir="$(cd "$(dirname "$0")" && pwd)"
fedora_root="$(dirname "$script_dir")"

echo ">>> Fedora $fedora_release rootfs для uke"
mkdir -p "$rootfs" "$outdir"

echo ">>> Пакеты @core"
dnf -y --installroot="$rootfs" --releasever="$fedora_release" \
    --use-host-config --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    @core \
    NetworkManager openssh-server openssh-clients \
    sudo chrony zram-generator python3 \
    alsa-ucm alsa-utils dtc kmod e2fsprogs \
    qcom-firmware atheros-firmware

echo ">>> Overlay"
cp -a "$fedora_root/rootfs/overlay/." "$rootfs/"

echo ">>> fstab / hostname / SELinux"
cat > "$rootfs/etc/fstab" <<FSTAB
UUID=$root_uuid / ext4 defaults 0 0
FSTAB
echo "uke-fedora" > "$rootfs/etc/hostname"
if [ -f "$rootfs/etc/selinux/config" ]; then
    sed -i 's/^SELINUX=.*/SELINUX=permissive/' "$rootfs/etc/selinux/config"
fi

echo ">>> Модули ядра"
if [ -d "$modules_src" ]; then
    mkdir -p "$rootfs/usr/lib/modules"
    cp -a "$modules_src/." "$rootfs/usr/lib/modules/"
    # depmod в installroot
    for m in "$rootfs"/usr/lib/modules/*/; do
        depmod -b "$rootfs" "$(basename "$m")" || true
    done
else
    echo "    WARN: нет $modules_src — модули не установлены" >&2
fi

echo ">>> Firmware"
if [ -f "$firmware_tar" ]; then
    tar xzf "$firmware_tar" -C "$rootfs"
else
    echo "    WARN: нет $firmware_tar" >&2
fi

echo ">>> USB gadget net (отладка)"
mkdir -p "$rootfs/etc/NetworkManager/system-connections"
cat > "$rootfs/etc/NetworkManager/system-connections/usb0.nmconnection" <<'NM'
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

echo ">>> Восстанавливаю владельца root"
chroot "$rootfs" /bin/sh -c 'chown -R root:root / 2>/dev/null' || true

echo ">>> Упаковка"
tar -C "$rootfs" -czf "$outdir/uke-fedora-rootfs.tar.gz" .
ls -la "$outdir/uke-fedora-rootfs.tar.gz"
