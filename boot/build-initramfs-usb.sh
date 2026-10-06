#!/usr/bin/env bash
# Initramfs with USB gadget support, a cleared framebuffer, and compact status output.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/build/initramfs-usb.lz4"
KVER="${KVER:-6.12.0-dirty}"
MODLIST="drivers/interconnect/qcom/qnoc-cliffs-usb.ko
drivers/clk/qcom/gdsc-regulator-uke.ko
drivers/clk/qcom/gcc-cliffs.ko
drivers/dma/qcom/gpi.ko
drivers/i2c/busses/i2c-qcom-geni.ko
drivers/usb/repeater/repeater-qti-pmic-eusb2-uke.ko
drivers/usb/phy/phy-msm-snps-eusb2-uke.ko
drivers/usb/dwc3/dwc3.ko
drivers/usb/dwc3/dwc3-qcom.ko
drivers/usb/gadget/libcomposite.ko
drivers/usb/gadget/function/u_ether.ko
drivers/usb/gadget/function/usb_f_rndis.ko
drivers/usb/gadget/function/usb_f_ecm.ko
drivers/usb/gadget/function/u_serial.ko
drivers/usb/gadget/function/usb_f_acm.ko
drivers/usb/gadget/function/usb_f_serial.ko
drivers/usb/gadget/legacy/g_serial.ko
drivers/ufs/host/ufs-qcom.ko
drivers/phy/qualcomm/phy-qcom-qmp-ufs.ko"

docker run --rm --network host -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
	-e MODLIST="$MODLIST" -e KVER="$KVER" -v "${ROOT}:/work" -w /work quay.io/fedora/fedora:44 bash -lc '
set -euo pipefail
rm -f /etc/yum.repos.d/*.repo; cp /work/rootfs/fedora-repos/*.repo /etc/yum.repos.d/
dnf -y install busybox cpio lz4 kmod >/dev/null
rm -rf /tmp/ir; mkdir -p /tmp/ir/bin /tmp/ir/proc /tmp/ir/sys /tmp/ir/dev /tmp/ir/newroot
MDIR="/tmp/ir/lib/modules/$KVER"; mkdir -p "$MDIR"
while read -r m; do
  [ -z "$m" ] && continue
  src="/work/build/ztsubaki/out/$m"
  if [ -f "$src" ]; then mkdir -p "$MDIR/$(dirname "$m")"; cp "$src" "$MDIR/$m"; else echo "missing required module: $m" >&2; exit 1; fi
done <<< "$MODLIST"
cp /work/kernel/modules.load "$MDIR/modules.load"
printf "%s\n" "drivers/usb/gadget/function/u_ether.ko" "drivers/usb/gadget/function/usb_f_rndis.ko" "drivers/usb/gadget/function/usb_f_ecm.ko" "drivers/ufs/host/ufs-qcom.ko" "drivers/phy/qualcomm/phy-qcom-qmp-ufs.ko" >> "$MDIR/modules.load"
depmod -b /tmp/ir "$KVER" 2>/dev/null || true
cp /usr/bin/busybox /tmp/ir/bin/busybox
cat > /tmp/ir/init <<"EOS"
#!/bin/busybox sh
/bin/busybox --install -s /bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mkdir -p /tmp /run /root
: > /tmp/mok; : > /tmp/mfail
while read -r m; do
    [ -z "$m" ] && continue
    [ "${m#\#}" != "$m" ] && continue
    mod="$(basename "$m" .ko)"
    if modprobe "$mod" 2>/dev/null; then echo "$mod" >> /tmp/mok; else echo "$mod" >> /tmp/mfail; fi
done < /lib/modules/$(uname -r)/modules.load
mount -t configfs none /sys/kernel/config 2>/dev/null || true
G=/sys/kernel/config/usb_gadget/g1
if mkdir -p "$G" 2>/dev/null; then
    echo 0x18d1 > "$G/idVendor"; echo 0x4e40 > "$G/idProduct"
    mkdir -p "$G/strings/0x409"; echo uke > "$G/strings/0x409/serialnumber"; echo uke > "$G/strings/0x409/manufacturer"; echo uke > "$G/strings/0x409/product"
    mkdir -p "$G/configs/c.1/strings/0x409"; echo cfg > "$G/configs/c.1/strings/0x409/configuration"
    mkdir -p "$G/functions/acm.usb0"
    mkdir -p "$G/functions/rndis.usb0" 2>/dev/null || mkdir -p "$G/functions/ecm.usb0" 2>/dev/null
    ln -sf "$G/functions/acm.usb0" "$G/configs/c.1/"
    [ -d "$G/functions/rndis.usb0" ] && ln -sf "$G/functions/rndis.usb0" "$G/configs/c.1/"
    [ -d "$G/functions/ecm.usb0" ] && ln -sf "$G/functions/ecm.usb0" "$G/configs/c.1/"
    udc="$(ls /sys/class/udc 2>/dev/null | head -1)"
    [ -n "$udc" ] && echo "$udc" > "$G/UDC"
    sleep 1; ip link set usb0 up 2>/dev/null; ip addr add 172.16.42.1/24 dev usb0 2>/dev/null
fi
# USB ACM shell for the host (picocom/screen on /dev/ttyACM0)
( while [ ! -c /dev/ttyGS0 ]; do sleep 0.2; done
  while true; do setsid sh -c "exec sh -i </dev/ttyGS0 >/dev/ttyGS0 2>&1"; sleep 1; done ) &
mkdir -p /newroot
for i in $(seq 1 50); do [ -b /dev/sda ] && break; sleep 0.2; done
dev=""; for x in $(cat /proc/cmdline); do case "$x" in root=*) dev="${x#root=}";; esac; done
rootdev=""
case "$dev" in
  UUID=*|LABEL=*) key="${dev#*=}"; for b in /dev/sda* /dev/mmcblk*; do [ -b "$b" ] && blkid "$b" 2>/dev/null | grep -q "$key" && { rootdev="$b"; break; }; done ;;
  /dev/*) rootdev="$dev" ;;
esac
[ -n "$rootdev" ] || for b in /dev/sda* /dev/mmcblk*; do [ -b "$b" ] && blkid "$b" 2>/dev/null | grep -q ext4 && { rootdev="$b"; break; }; done
# --- clear the framebuffer and print compact status ---
dmesg -n 1 2>/dev/null
printf "\033[2J\033[H"
{
echo "===== UKE STATUS ====="
echo "kernel : $(uname -r)"
echo "mods ok: $(wc -l < /tmp/mok)   fail: $(tr "\n" " " < /tmp/mfail)"
echo "udc    : $(ls /sys/class/udc 2>/dev/null | tr "\n" " ")"
echo "usb0   : $(ip -o addr show usb0 2>/dev/null | awk "{print \$4}")"
echo "ext4   : $(blkid 2>/dev/null | grep -c ext4) found"
echo "rootdev: ${rootdev:-none}"
echo "======================"
} | tee /status.txt
if [ -n "$rootdev" ]; then
    echo "uke: mount $rootdev -> /newroot"
    if mount -t ext4 -o rw "$rootdev" /newroot; then
        echo "uke: switch_root to systemd"
        exec switch_root /newroot /usr/lib/systemd/systemd
    fi
fi
{
echo "--- dt ---"
for n in /proc/device-tree/soc/ufshc@1d84000 /proc/device-tree/soc/ufsphy_mem@1d80000; do
  [ -d "$n" ] || { echo "no $n"; continue; }
  echo "$(basename $n): compat=$(tr "\0" " " < $n/compatible 2>/dev/null) status=$(tr "\0" " " < $n/status 2>/dev/null)"
done
echo "--- probes ---"
dmesg | grep -iE "ufs|ufshcd|qmp|gcc|icc|noc|regulator|rpmh|spmi_pmic_arb|dwc3|deferred" | tail -10
echo "--- deferred ---"
mount -t debugfs none /sys/kernel/debug 2>/dev/null
head -12 /sys/kernel/debug/devices_deferred 2>/dev/null
echo "--- bind ---"
for d in 1d84000.ufshc 1d80000.ufsphy; do echo "$d: $(basename "$(readlink /sys/bus/platform/devices/$d/driver 2>/dev/null)" 2>/dev/null || echo -)"; done
echo "--- regdrv ---"
echo "uke: $(ls /sys/bus/platform/drivers/qcom,rpmh-regulator/ 2>/dev/null | wc -l) mainline: $(ls /sys/bus/platform/drivers/qcom-rpmh-regulator/ 2>/dev/null | wc -l)"
dmesg | grep -iE "rpmh|regulator|cmd.db|resource" | tail -8
echo "--- rpmh ---"
echo "rsc: $(basename "$(readlink /sys/bus/platform/devices/17a00000.rsc/driver 2>/dev/null)" 2>/dev/null || echo -)"
echo "regdrv: $(ls -d /sys/bus/platform/drivers/*rpmh* 2>/dev/null | tr "\n" " ")"
echo "regdevs: $(ls -d /sys/bus/platform/devices/*rpmh-regulator* 2>/dev/null | wc -l) regs: $(ls /sys/class/regulator/ 2>/dev/null | wc -l)"
} | tee -a /status.txt
echo "uke: shell (ttyGS0/tty0)"
exec setsid cttyhack sh -i
EOS
chmod +x /tmp/ir/init
( cd /tmp/ir && find . -print0 | cpio --null -o -H newc 2>/dev/null | lz4 -l -12 -f - /work/build/initramfs-usb.lz4 >/dev/null )
chown "$HOST_UID:$HOST_GID" /work/build/initramfs-usb.lz4
'
ls -la "$OUT"
