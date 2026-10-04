#!/usr/bin/env bash
# Минимальный busybox-initramfs для init_boot (ztsubaki-схема, влезает в 8 МиБ).
# Монтирует Fedora root по UUID из cmdline и switch_root в systemd.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/build/initramfs-minimal.lz4"

docker run --rm --network host -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -v "${ROOT}:/work" -w /work quay.io/fedora/fedora:44 bash -lc '
set -euo pipefail
rm -f /etc/yum.repos.d/*.repo
cp /work/rootfs/fedora-repos/*.repo /etc/yum.repos.d/
dnf -y install busybox cpio lz4 >/dev/null
rm -rf /tmp/ir
mkdir -p /tmp/ir/bin /tmp/ir/proc /tmp/ir/sys /tmp/ir/dev /tmp/ir/newroot /tmp/ir/etc
cp /usr/bin/busybox /tmp/ir/bin/busybox
if ldd /usr/bin/busybox >/dev/null 2>&1; then
    ldd /usr/bin/busybox | grep -oE "/[^ ]+\.so[^ ]*" | sort -u | while read -r l; do
        mkdir -p "/tmp/ir$(dirname "$l")"
        cp -a "$l" "/tmp/ir$l"
    done
fi
cat > /tmp/ir/init <<"EOS"
#!/bin/busybox sh
/bin/busybox --install -s /bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
# USB gadget: ACM serial console + RNDIS net (отладка)
mount -t configfs none /sys/kernel/config 2>/dev/null || true
G=/sys/kernel/config/usb_gadget/g1
if mkdir -p "$G" 2>/dev/null; then
    echo 0x18d1 > "$G/idVendor" 2>/dev/null
    echo 0x4e40 > "$G/idProduct" 2>/dev/null
    mkdir -p "$G/strings/0x409"
    echo uke > "$G/strings/0x409/serialnumber" 2>/dev/null
    echo uke > "$G/strings/0x409/manufacturer" 2>/dev/null
    echo uke > "$G/strings/0x409/product" 2>/dev/null
    mkdir -p "$G/configs/c.1/strings/0x409"
    echo cfg > "$G/configs/c.1/strings/0x409/configuration" 2>/dev/null
    mkdir -p "$G/functions/acm.usb0" "$G/functions/rndis.usb0"
    ln -sf "$G/functions/acm.usb0" "$G/configs/c.1/" 2>/dev/null
    ln -sf "$G/functions/rndis.usb0" "$G/configs/c.1/" 2>/dev/null
    udc="$(ls /sys/class/udc 2>/dev/null | head -1)"
    [ -n "$udc" ] && echo "$udc" > "$G/UDC" 2>/dev/null
    sleep 1
    ip link set usb0 up 2>/dev/null || true
    ip addr add 172.16.42.1/24 dev usb0 2>/dev/null || true
fi
mkdir -p /newroot
root=""
for x in $(cat /proc/cmdline); do
    case "$x" in root=*) root="${x#root=}" ;; esac
done
[ -n "$root" ] || root="LABEL=uke_root"
echo "uke-initramfs: root=$root"
dev=""
i=0
while [ $i -lt 40 ]; do
    case "$root" in
        UUID=*) dev="$(blkid -U "${root#UUID=}" 2>/dev/null || true)" ;;
        LABEL=*) dev="$(blkid -L "${root#LABEL=}" 2>/dev/null || true)" ;;
        *) dev="$root" ;;
    esac
    [ -n "$dev" ] && break
    sleep 1; i=$((i+1))
done
echo "uke-initramfs: dev=$dev"
[ -n "$dev" ] || { echo "root device not found"; exec sh; }
mount -t ext4 -o rw "$dev" /newroot || { echo "mount failed"; exec sh; }
exec switch_root /newroot /usr/lib/systemd/systemd
EOS
chmod +x /tmp/ir/init
( cd /tmp/ir && find . -print0 | cpio --null -o -H newc 2>/dev/null | lz4 -l -12 -f - /work/build/initramfs-minimal.lz4 >/dev/null )
chown "$HOST_UID:$HOST_GID" /work/build/initramfs-minimal.lz4
'
ls -la "$OUT"
echo "размер: $(stat -c %s "$OUT") байт (лимит init_boot 8388608)"
