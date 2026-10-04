#!/usr/bin/env bash
# Собрать dracut-initramfs для uke в arm64 Fedora-контейнере.
# Требует собранных модулей: build/uke-modules/usr/lib/modules/<kver> (kernel/build.sh).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${ROOT}/build/uke-modules"
IMAGE="${ROOT}/build/uke-build/arch/arm64/boot/Image"
OUT="${ROOT}/build/initramfs.img"

[ -d "${STAGE}/usr/lib/modules" ] || { echo "нет модулей: запусти kernel/build.sh" >&2; exit 1; }
KVER="${KVER:-$(ls "${STAGE}/usr/lib/modules" | head -1)}"
echo "KVER: ${KVER}"

docker run --rm --network host -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" -v "${ROOT}:/work" -w /work quay.io/fedora/fedora:44 \
    bash -lc "
set -euxo pipefail
dnf -y install dracut cpio lz4 kmod iproute >/dev/null
# модули ядра
mkdir -p /usr/lib/modules
rm -rf /usr/lib/modules/${KVER}
cp -a /work/build/uke-modules/usr/lib/modules/${KVER} /usr/lib/modules/
# kernel image (dracut любит его видеть)
mkdir -p /boot
cp /work/build/uke-build/arch/arm64/boot/Image /boot/vmlinuz-${KVER}
# firmware (GPU и др.) в /usr/lib/firmware
tar xzf /work/rootfs/firmware.tar.gz -C /usr 2>/dev/null || true
# dracut-модуль + конфиг
cp -a /work/boot/dracut/90uke-usbnet /usr/lib/dracut/modules.d/
cp /work/boot/dracut/dracut.conf.d/uke.conf /usr/lib/dracut/dracut.conf.d/
dracut --kver ${KVER} --force /work/build/initramfs.img
chown $HOST_UID:$HOST_GID /work/build/initramfs.img
"
ls -la "${OUT}"
